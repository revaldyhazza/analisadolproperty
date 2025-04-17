import streamlit as st
import pandas as pd
import plotly.express as px
import datetime as dt

# Page configuration
st.set_page_config(
    page_title="Dashboard Analisa DoL",
    page_icon="🚨",
    layout="wide",
)

# Title and instructions
st.markdown("# 🚨 Dashboard Analisa DoL CoB Property")
st.markdown("""
    <div style='text-align: justify'>
    📍 Untuk pengalaman yang lebih baik, tutup kembali sidebar setelah mengaplikasikan filter dan 
    membuat tampilan menjadi wide mode. Direkomendasikan juga untuk membuka menggunakan Laptop/PC
    </div>
""", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# Function to read and clean Excel files
@st.cache_data
def read_excel(file):
    df = pd.read_excel(file)
    df = df.drop(columns=[col for col in df.columns if str(col).startswith("Unnamed")])
    return df

st.write("# ⬆️ Upload dan Manipulasi Data")
# 1. Upload Klaim data
file_klaim = st.file_uploader("📂 Upload Data Klaim (Excel)", type="xlsx", key="klaim")
if file_klaim:
    df_klaim = read_excel(file_klaim)
    df_klaim['Sumber Data'] = 'Klaim'
    # Deduplicate based on key columns
    key_columns_klaim = ['NO POLIS', 'NO SERTIFIKAT', 'NO KLAIM']
    df_klaim = df_klaim.drop_duplicates(subset=key_columns_klaim, keep='first')
    st.write("### 1️⃣ Preview Data Klaim")
    st.info(f"🔍 Data Klaim memiliki **{len(df_klaim):,} baris setelah deduplikasi.**")
    st.dataframe(df_klaim.head(), hide_index=True)

# 2. Upload OS Klaim data
file_os = st.file_uploader("📂 Upload Data Outstanding Klaim (Excel)", type="xlsx", key="os")
if file_os:
    df_os_klaim = read_excel(file_os)
    df_os_klaim['Sumber Data'] = 'OS Klaim'
    # Deduplicate based on key columns
    key_columns_osklaim = ['CLAIM NO']
    df_os_klaim = df_os_klaim.drop_duplicates(subset=key_columns_osklaim, keep='first')
    st.write("### 2️⃣ Preview Data Outstanding Klaim")
    st.info(f"🔍 Data OS Klaim memiliki **{len(df_os_klaim):,} baris setelah deduplikasi.**")
    st.dataframe(df_os_klaim.head(), hide_index=True)

# Process combined data if both files are uploaded
if file_klaim and file_os:
    # Normalize column names
    df_klaim_norm = df_klaim.rename(columns={
        'NO POLIS': 'POLIS',
        'NO KLAIM': 'KLAIM'
    })
    df_os_klaim_norm = df_os_klaim.rename(columns={
        'POLICY NO': 'POLIS',
        'CLAIM NO': 'KLAIM'
    })

    # Add dummy SERTIFIKAT column if missing in OS Klaim
    if 'SERTIFIKAT' not in df_os_klaim_norm.columns:
        df_os_klaim_norm['SERTIFIKAT'] = ''

    # Create unique key for comparison
    df_klaim_norm['key'] = df_klaim_norm['POLIS'].astype(str) + '-' + df_klaim_norm['KLAIM'].astype(str)
    df_os_klaim_norm['key'] = df_os_klaim_norm['POLIS'].astype(str) + '-' + df_os_klaim_norm['KLAIM'].astype(str)

    # Classify records
    klaim_keys = set(df_klaim_norm['key'])
    os_klaim_keys = set(df_os_klaim_norm['key'])
    klaim_only = klaim_keys - os_klaim_keys
    os_klaim_only = os_klaim_keys - klaim_keys
    klaim_dan_os = klaim_keys & os_klaim_keys

    # Add Kategori column
    df_klaim_norm['Kategori'] = df_klaim_norm['key'].apply(
        lambda x: 'Klaim + OS Klaim' if x in klaim_dan_os else 'Klaim'
    )
    df_os_klaim_norm['Kategori'] = df_os_klaim_norm['key'].apply(
        lambda x: 'Klaim + OS Klaim' if x in klaim_dan_os else 'OS Klaim'
    )

    # Combine dataframes
    df_gabungan = pd.concat([df_klaim_norm, df_os_klaim_norm], ignore_index=True)
    df_gabungan = df_gabungan.drop(columns=[
        "SISTEM", "NAMA FILE", "AY", "COB", "TOC", "UY", "VALUE AT RISK", 
        "TUNTUTAN_KLAIM", "ANR", "KLAIM REAS", "TOTAL_LOSS", "key", "Sumber Data", 
        "BISNIS", "POLICY_BRANCH", "LOB", "UW_YEAR", "uw", "UW_YEAR.1", "REGDATE", 
        "CURRENCY", "Net OS Klaim", "Reas", "DY", "JKW", "LT/ST", "COB", "SERTIFIKAT", 
        "COB Eng"
    ], errors='ignore')

    # Convert date columns
    df_gabungan["INCEPTION DATE"] = pd.to_datetime(df_gabungan["INCEPTION DATE"], errors='coerce')
    df_gabungan["EXPIRY DATE"] = pd.to_datetime(df_gabungan["EXPIRY DATE"], errors='coerce')
    df_gabungan["DOL"] = pd.to_datetime(df_gabungan["DOL"], errors='coerce')

    # Define Cause of Loss mapping
    mapping_cause_of_loss = {
        "Angin Topan": "Act of God",
        "Badai": "Act of God",
        "Gempa Bumi": "Act of God",
        "Longsor": "Act of God",
        "Petir": "Act of God",
        "Banjir": "Act of God",
        "Letusan Gunung Berapi": "Act of God",
        "Kebakaran": "Kebakaran",
        "Huru-Hara": "Huru-hara, Kerusuhan, Kebongkaran",
        "Kerusuhan": "Huru-hara, Kerusuhan, Kebongkaran",
        "Kebongkaran": "Huru-hara, Kerusuhan, Kebongkaran",
        "Hubungan Arus Pendek": "Hubungan Arus Pendek",
        "Ledakan": "Ledakan",
        "Rusak karena Air": "Water Damage",
        "Tertabrak Kendaraan atau Alat Angkut": "Vehicle Impact",
        "Lain-Lain": "Lain-lain"
    }

    # Apply mappings and calculations
    df_gabungan["Kategori Cause of Loss"] = df_gabungan["CAUSE OF LOSS"].map(mapping_cause_of_loss)
    df_gabungan["Coverage"] = df_gabungan.get("TOC_MOD", "")
    df_gabungan = df_gabungan.drop(columns=["TOC_MOD"], errors='ignore')
    df_gabungan["Bulan ke-"] = (
        (df_gabungan['DOL'].dt.year - df_gabungan['INCEPTION DATE'].dt.year) * 12 + 
        (df_gabungan['DOL'].dt.month - df_gabungan['INCEPTION DATE'].dt.month)
    )

    # Format dates
    df_gabungan["INCEPTION DATE"] = df_gabungan["INCEPTION DATE"].dt.strftime('%Y-%m-%d')
    df_gabungan["DOL"] = df_gabungan["DOL"].dt.strftime('%Y-%m-%d')
    df_gabungan["EXPIRY DATE"] = df_gabungan["EXPIRY DATE"].dt.strftime('%Y-%m-%d')

    # Create Range Terjadi Klaim
    bins = [-1, 3, 6, 9, 12, float('inf')]
    labels = ['0-3', '>3-6', '>6-9', '>9-12', '>12']
    df_gabungan['Range Terjadi Klaim'] = pd.cut(df_gabungan['Bulan ke-'], bins=bins, labels=labels)

    # Drop rows with missing critical columns
    df_gabungan = df_gabungan.dropna(subset=['Bulan ke-', 'Range Terjadi Klaim', 'DOL'])

    # Sidebar filters
    st.sidebar.header("Filter Data")

    # Filter Range Terjadi Klaim
    rangeklaim_options = sorted(df_gabungan['Range Terjadi Klaim'].astype(str).unique())
    selected_rangeklaim = st.sidebar.multiselect(
        "Pilih Range Terjadinya Klaim",
        options=rangeklaim_options,
        default=[]  # No default selection
    )

    # Filter Date Range for DOL
    df_gabungan['DOL'] = pd.to_datetime(df_gabungan['DOL'], errors='coerce')
    min_date = df_gabungan['DOL'].min().date()
    max_date = df_gabungan['DOL'].max().date()
    date_range = st.sidebar.date_input(
        "Pilih Rentang Date of Loss (DOL)",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    # Filter Bulan ke-
    min_bulan = int(df_gabungan['Bulan ke-'].min())
    max_bulan = int(df_gabungan['Bulan ke-'].max())
    range_bulan = st.sidebar.slider(
        'Bulan Ke-',
        min_value=min_bulan,
        max_value=max_bulan,
        value=(min_bulan, max_bulan),
        step=1
    )

    # Apply filters
    df_filtered = df_gabungan.copy()
    if selected_rangeklaim:
        df_filtered = df_filtered[df_filtered['Range Terjadi Klaim'].astype(str).isin(selected_rangeklaim)]
    
    # Apply date range filter
    if len(date_range) == 2:  # Ensure both start and end dates are selected
        start_date, end_date = date_range
        df_filtered = df_filtered[
            (df_filtered['DOL'].dt.date >= start_date) & 
            (df_filtered['DOL'].dt.date <= end_date)
        ]

    # Apply Bulan ke- filter
    df_filtered = df_filtered[
        (df_filtered['Bulan ke-'] >= range_bulan[0]) & 
        (df_filtered['Bulan ke-'] <= range_bulan[1])
    ]

    # Display filtered data
    st.write("### 3️⃣ Filtered Data")
    if len(df_filtered) > 0:
        st.info(f"🔍 Data setelah filter memiliki **{len(df_filtered):,} baris.**")
        st.dataframe(df_filtered, hide_index=True)
    else:
        st.warning("⚠️ Tidak ada data yang sesuai dengan filter yang dipilih.")

    # Summary of Kategori (filtered)
    kategori_summary_filtered = df_filtered['Kategori'].value_counts().reset_index()
    kategori_summary_filtered.columns = ['Kategori', 'Jumlah']
    st.write("### 4️⃣ Ringkasan Jumlah per Kategori (Filtered)")
    st.dataframe(kategori_summary_filtered, hide_index=True)
    
    st.write("# 📊 Visualisasi dan Deskriptif Statistik")
    
    st.write("### 1️⃣ Statistik Deskriptif")
    st.dataframe(df_filtered.drop(columns=["NO SERTIFIKAT", "DOL"]).describe(), use_container_width=True)
    
    jumlah_klaim = df_filtered.groupby(['Range Terjadi Klaim', 'Kategori Cause of Loss']).size().reset_index(name='Jumlah Klaim')
    amount_klaim = df_filtered.groupby(['Range Terjadi Klaim', 'Kategori Cause of Loss'])['CLAIM AMOUNT (IDR)'].sum().reset_index()
    amount_klaim['Amount (M)'] = amount_klaim['CLAIM AMOUNT (IDR)'] / 1_000_000
    
    amount_klaim = amount_klaim.rename(columns={
    'Range Terjadi Klaim': 'Range_Klaim',
    'Kategori Cause of Loss': 'Kategori_Cause',
    'Amount (M)': 'Amount_M'
    })
    
    jumlah_klaim = jumlah_klaim.rename(columns={
    'Range Terjadi Klaim': 'Range_Klaim',
    'Kategori Cause of Loss': 'Kategori_Cause',
    'Jumlah Klaim': 'Jumlah_Klaim'
    })

    col1, col2 = st.columns(2)

    with col1:
            st.markdown("### 💰 Amount Klaim")
            st.write(amount_klaim)

    with col2:
            st.markdown("### 📊 Jumlah Klaim")
            st.write(jumlah_klaim)
            
    col1, col2 = st.columns(2)
    
    with col1:
        fig_amount = px.bar(
            amount_klaim,
            x='Range_Klaim',
            y='CLAIM AMOUNT (IDR)',
            color='Kategori_Cause',
            barmode='group',
        )
        fig_amount.update_layout(
            height=500,
            yaxis_title="",
            xaxis_title="",
            margin=dict(t=30, b=30, l=0, r=0),
            title_font_size=16,
            title="Amount of Claim"
        )
        
        fig_amount.update_layout(
                legend=dict(
                orientation="v",
                yanchor="middle",
                y=0.5,
                xanchor="left",
                x=1.0
            )
        )
        st.plotly_chart(fig_amount, use_container_width=True)

    with col2:
        fig_count = px.bar(
            jumlah_klaim,
            x='Range_Klaim',
            y='Jumlah_Klaim',
            color='Kategori_Cause',
            barmode='group',
            title=None
        )
        fig_count.update_layout(
            height=500,
            yaxis_title="",
            xaxis_title="",
            margin=dict(t=30, b=30, l=0, r=0),
            title_font_size=16,
            title= "Number of Claim"
        )
        fig_count.update_layout(
                legend=dict(
                orientation="v",
                yanchor="middle",
                y=0.5,
                xanchor="left",
                x=1.0
            )
        )
        st.plotly_chart(fig_count, use_container_width=True)
    
    klaim_sev = df_filtered.groupby("CAUSE OF LOSS")["CLAIM AMOUNT (IDR)"].sum().nlargest(10).reset_index()
    klaim_sev.columns = ["Causeofloss", "Severity"]
    
    klaim_freq = (
    df_filtered["CAUSE OF LOSS"]
    .value_counts()
    .nlargest(10)
    .reset_index()
    )
    klaim_freq.columns = ["Causeofloss", "Frequency"]
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
            <style>
                .custom-title {
                    text-align: center;
                    margin-bottom: -20px;
                    position: relative;
                    top: 10px;
                }
            </style>
            <h4 class="custom-title">10 Sumber Klaim Terbesar Berdasarkan Cause of Loss</h4>
        """, unsafe_allow_html=True)

        colors = [
            "#7a3300", "#a34700", "#cc5c00", "#e67300", "#ff8000",
            "#ff9933", "#ffb366", "#ffcc99", "#ffe0cc", "#fff5e6"
        ]
        fig1 = px.bar(
            klaim_sev,
            x="Severity",
            y="Causeofloss",
            orientation="h",
            text="Severity",
            color="Causeofloss",
            color_discrete_sequence=colors
        )
        fig1.update_layout(
            width=900,
            height=500,
            margin=dict(l=0, r=50, t=10, b=50),
            font=dict(size=14),
            xaxis_title=None,
            yaxis_title=None,
            showlegend=False,
        )
        fig1.update_traces(textposition="auto")
        fig1.update_traces(texttemplate="%{text:,.0f}")
        st.plotly_chart(fig1)
        
    with col2:
        st.markdown("""
            <style>
                .custom-title {
                    text-align: center;
                    margin-bottom: -20px;
                    position: relative;
                    top: 10px;
                }
            </style>
            <h4 class="custom-title">10 Sumber Klaim Terbanyak Berdasarkan Cause of Loss</h4>
        """, unsafe_allow_html=True)

        colors = [
            "#7a3300", "#a34700", "#cc5c00", "#e67300", "#ff8000",
            "#ff9933", "#ffb366", "#ffcc99", "#ffe0cc", "#fff5e6"
        ]
        fig1 = px.bar(
            klaim_freq,
            x="Frequency",
            y="Causeofloss",
            orientation="h",
            text="Frequency",
            color="Causeofloss",
            color_discrete_sequence=colors
        )
        fig1.update_layout(
            width=900,
            height=500,
            margin=dict(l=0, r=50, t=10, b=50),
            font=dict(size=14),
            xaxis_title=None,
            yaxis_title=None,
            showlegend=False
        )
        fig1.update_traces(textposition="outside")
        st.plotly_chart(fig1)