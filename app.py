import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import mplstereonet

# Konfigurasi Halaman
st.set_page_config(
    page_title="Structural Geology & Fault Kinematics", 
    layout="wide",
    page_icon="📐"
)

# ------------------------------------------
# FUNGSI KONVERSI NOTASI GEOLOGI LENGKAP
# ------------------------------------------
def get_ddir_azimuth(strike):
    """Menghitung Azimuth Dip Direction berdasarkan Right-Hand Rule (RHR)"""
    return (strike + 90) % 360

def azimuth_to_quadrant_cardinal(azimuth):
    """Mengonversi azimuth sudut (0-360) ke mata angin kuadran (N, NE, E, SE, S, SW, W, NW)"""
    dirs = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    idx = int(round(azimuth / 45.0)) % 8
    return dirs[idx]

def format_geology_notation(strike, dip):
    """
    Mengonversi Strike dan Dip menjadi format geologi bidang lengkap:
    Contoh: N 87° E / 45° SW
    """
    strike = strike % 360
    ddir_azimuth = get_ddir_azimuth(strike)
    ddir_cardinal = azimuth_to_quadrant_cardinal(ddir_azimuth)
    formatted_str = f"N {strike:.0f}° E / {dip:.0f}° {ddir_cardinal}"
    return formatted_str

def format_vector_notation(plunge, trend):
    """
    Mengonversi Plunge dan Trend menjadi format vektor/garis tegasan geologi lengkap:
    Contoh: 12° / N 119° E
    """
    plunge_val = plunge[0] if isinstance(plunge, (list, np.ndarray)) else plunge
    trend_val = trend[0] if isinstance(trend, (list, np.ndarray)) else trend
    trend_val = trend_val % 360
    
    # Menghitung bidang tegak lurus (pole plane) untuk sigma
    plane_strike = (trend_val - 90) % 360
    plane_dip = 90 - plunge_val
    plane_notag = format_geology_notation(plane_strike, plane_dip)
    
    formatted_vec = f"{plunge_val:.0f}° / N {trend_val:.0f}° E"
    return formatted_vec, plane_notag


# Header Aplikasi
st.title("📐 Analisis Kinematik Sesar (Sesar Utama Merah)")
st.write(
    "Aplikasi geologi struktur untuk analisis pergerakan sesar dengan notasi orientasi lengkap "
    "garis tegasan & bidang (*N ...° E / ...° SW*), **Bidang Bantu (Auxiliary Plane)**, "
    "pasangan *Conjugate Shear Fractures* (**SF1** & **SF2**), serta *Gash Fracture* (**GF**)."
)

st.markdown("---")

# Layout Input dan Output
c_in, c_out = st.columns([1, 1])

with c_in:
    st.subheader("🔍 1. Data Sesar Utama & Gores-Garis")

    f_strike = st.number_input("Strike Sesar Utama (°):", 0.0, 360.0, 45.0, key="f_strike")
    f_dip = st.number_input("Dip Sesar Utama (°):", 0.0, 90.0, 60.0, key="f_dip")
    
    f_notag = format_geology_notation(f_strike, f_dip)
    st.caption(f"🧭 Kedudukan Sesar Utama: **{f_notag}**")
    
    # Fitur Pitch / Rake Opsional
    has_pitch = st.checkbox("Memiliki Data Pitch / Rake Gores-Garis", value=True)
    
    if has_pitch:
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            pitch = st.number_input("Nilai Pitch / Rake (°):", 0.0, 90.0, 30.0, key="pitch_val")
        with col_p2:
            pitch_quadrant = st.selectbox("Arah Pitch dari Strike:", ["Northeast / East", "Northwest / West", "Southwest / West", "Southeast / East"], index=0)
        
        vertical_sense = st.radio("Sifat Pergerakan Vertikal (Berdasarkan Indikator Sesar):", 
                                  ["Naik (Reverse/Thrust)", "Turun (Normal)"], index=0)
    else:
        pitch = None
        st.info("ℹ️ Pitch diatur **N/A**. Pergerakan dan kinematik akan dihitung otomatis berbasis vektor tegasan (SF & GF).")

    st.markdown("---")
    st.subheader("🔍 2. Pasangan Shear Fracture (SF1 & SF2)")
    
    col_sf1, col_sf2 = st.columns(2)
    with col_sf1:
        st.write("**Shear Fracture 1 (SF1):**")
        sf1_strike = st.number_input("Strike SF1 (°):", 0.0, 360.0, 30.0, key="sf1_str")
        sf1_dip = st.number_input("Dip SF1 (°):", 0.0, 90.0, 70.0, key="sf1_dip")
        sf1_notag = format_geology_notation(sf1_strike, sf1_dip)
        st.caption(f"🧭 SF1: **{sf1_notag}**")
        
    with col_sf2:
        st.write("**Shear Fracture 2 (SF2):**")
        sf2_strike = st.number_input("Strike SF2 (°):", 0.0, 360.0, 90.0, key="sf2_str")
        sf2_dip = st.number_input("Dip SF2 (°):", 0.0, 90.0, 80.0, key="sf2_dip")
        sf2_notag = format_geology_notation(sf2_strike, sf2_dip)
        st.caption(f"🧭 SF2: **{sf2_notag}**")

    st.markdown("---")
    st.subheader("🔍 3. Data Gash Fracture (GF)")
    gf_strike = st.number_input("Strike Gash Fracture / GF (°):", 0.0, 360.0, 150.0, key="gf_str")
    gf_dip = st.number_input("Dip Gash Fracture / GF (°):", 0.0, 90.0, 85.0, key="gf_dip")
    gf_notag = format_geology_notation(gf_strike, gf_dip)
    st.caption(f"🧭 GF: **{gf_notag}**")


# ------------------------------------------
# KALKULASI VEKTOR TEGASAN & BIDANG BANTU
# ------------------------------------------
# 1. Perpotongan SF1 dan SF2 -> Sumbu Sigma 2 (Neutral / B-Axis)
s2_plunge, s2_trend = mplstereonet.plane_intersection(sf1_strike, sf1_dip, sf2_strike, sf2_dip)

# 2. Vektor Tegasan Utama dari Pole GF:
s1_plunge, s1_trend = mplstereonet.pole(gf_strike, gf_dip)
s3_plunge, s3_trend = mplstereonet.pole((gf_strike + 90) % 360, gf_dip)

# 3. Perhitungan Net-Slip dan Bidang Bantu (Auxiliary Plane)
if has_pitch:
    # Menghitung Rake Vector Sesar Utama -> Vektor Net-Slip
    rake_sign = pitch if ("East" in pitch_quadrant or "North" in pitch_quadrant) else -pitch
    netslip_plunge, netslip_trend = mplstereonet.rake(f_strike, f_dip, rake_sign)
    aux_strike = (netslip_trend[0] - 90) % 360
    aux_dip = 90 - netslip_plunge[0]
else:
    # Perpotongan Sesar Utama dan Bidang Tegas B-Axis/Auxiliary sebagai Estimasi Net-Slip
    aux_strike = (f_strike + 90) % 360
    aux_dip = 90 - f_dip
    netslip_plunge, netslip_trend = mplstereonet.plane_intersection(f_strike, f_dip, aux_strike, aux_dip)

netslip_vec_str, _ = format_vector_notation(netslip_plunge, netslip_trend)
aux_notag = format_geology_notation(aux_strike, aux_dip)

# Format Vektor Tegasan Sigma
s1_vec_str, s1_plane_str = format_vector_notation(s1_plunge, s1_trend)
s2_vec_str, s2_plane_str = format_vector_notation(s2_plunge, s2_trend)
s3_vec_str, s3_plane_str = format_vector_notation(s3_plunge, s3_trend)

# Rejim Tektonik (Anderson, 1951)
if s1_plunge[0] > 60:
    anderson_regime = "Sesar Normal (Normal Faulting Regime)"
elif s1_plunge[0] < 30 and s3_plunge[0] < 30:
    anderson_regime = "Sesar Mendatar (Strike-Slip Faulting Regime)"
else:
    anderson_regime = "Sesar Naik / Anjak (Thrust Faulting Regime)"

# ------------------------------------------
# LOGIKA EVALUASI PERGERAKAN (DENGAN / TANPA PITCH)
# ------------------------------------------
if has_pitch:
    if "East" in pitch_quadrant or "North" in pitch_quadrant:
        horiz_label = "Mengiri (Sinistral)"
        is_dextral = False
    else:
        horiz_label = "Menganan (Dextral)"
        is_dextral = True
    
    is_reverse = "Naik" in vertical_sense
    vert_label = "Naik" if is_reverse else "Turun"
    pitch_calc_val = pitch
else:
    is_reverse = s1_plunge[0] < 45 and s3_plunge[0] > 45
    vert_label = "Naik" if is_reverse else "Turun"
    
    strike_diff = (f_strike - s1_trend[0]) % 180
    if 0 < strike_diff < 90:
        horiz_label = "Menganan (Dextral)"
        is_dextral = True
    else:
        horiz_label = "Mengiri (Sinistral)"
        is_dextral = False

    pitch_calc_val = 45.0 if s1_plunge[0] < 45 and s3_plunge[0] < 45 else 80.0

# 1. Penamaan Deskriptif Sederhana
simple_name = f"Sesar {horiz_label.split(' ')[0]} - {vert_label}"

# 2. Klasifikasi Rickard (1972)
def get_rickard_classification(dip, pitch_val, is_rev, is_dex):
    if pitch_val <= 10:
        return "Right-Slip Fault" if is_dex else "Left-Slip Fault"
    elif pitch_val >= 80:
        return "Reverse-Slip Fault" if is_rev else "Normal-Slip Fault"
    elif 10 < pitch_val < 45:
        if is_dex and is_rev:
            return "Right-Reverse Slip Fault"
        elif is_dex and not is_rev:
            return "Right-Normal Slip Fault"
        elif not is_dex and is_rev:
            return "Left-Reverse Slip Fault"
        else:
            return "Left-Normal Slip Fault"
    else:
        if is_dex and is_rev:
            return "Reverse-Right Slip Fault"
        elif is_dex and not is_rev:
            return "Normal-Right Slip Fault"
        elif not is_dex and is_rev:
            return "Reverse-Left Slip Fault"
        else:
            return "Normal-Left Slip Fault"

rickard_name = get_rickard_classification(f_dip, pitch_calc_val, is_reverse, is_dextral)
if not has_pitch:
    rickard_name += " (Estimasi - Pitch N/A)"


# Output di Kolom Kanan
with c_out:
    st.subheader("🎯 Hasil Penamaan Sesar & Kinematik")
    
    # Kedudukan Sesar Utama & Bidang Bantu
    col_k1, col_k2 = st.columns(2)
    with col_k1:
        st.markdown(f"**Sesar Utama:** `{f_notag}`")
    with col_k2:
        st.markdown(f"**Bidang Bantu:** `{aux_notag}`")
    
    # Bagian 1: Penamaan Deskriptif
    st.info(f"### 1. Penamaan Sesar (Deskriptif):\n# **{simple_name}**")
    
    # Bagian 2: Klasifikasi Rickard (1972)
    st.success(f"### 2. Klasifikasi Sesar (Rickard, 1972):\n# **{rickard_name}**")

    st.markdown("---")
    st.write(f"**Rejim Tektonik Utama (Anderson, 1951):** `{anderson_regime}`")

    # Display Vektor Tegasan Utama (Sigma 1, 2, 3) & Net-Slip
    col_s1, col_s2, col_s3 = st.columns(3)
    with col_s1:
        st.info(f"**$\sigma_1$ (Kompresi):**\n- Vektor: **{s1_vec_str}**\n- Pole: **{s1_plane_str}**")
    with col_s2:
        st.warning(f"**$\sigma_2$ (Netral):**\n- Vektor: **{s2_vec_str}**\n- Pole: **{s2_plane_str}**")
    with col_s3:
        st.error(f"**$\sigma_3$ (Ekstensi):**\n- Vektor: **{s3_vec_str}**\n- Pole: **{s3_plane_str}**")

    st.markdown(f"📌 **Vektor Net-Slip:** `{netslip_vec_str}`")

    st.markdown("---")
    st.subheader("📊 Stereonet Wulff Net")

    fig_sf, ax_sf = plt.subplots(figsize=(6, 6), subplot_kw={'projection': 'stereonet'})

    # Plot Sesar Utama (GARIS MERAH TEGAS)
    ax_sf.plane(f_strike, f_dip, color='red', linestyle='-', linewidth=2.8, label=f'Sesar Utama ({f_notag})')
    
    # Plot Bidang Lainnya (Garis Tegas Berwarna)
    ax_sf.plane(aux_strike, aux_dip, color='blue', linestyle='-', linewidth=2.0, label=f'Bidang Bantu ({aux_notag})')
    ax_sf.plane(sf1_strike, sf1_dip, color='green', linestyle='-', linewidth=1.5, label=f'SF1 ({sf1_notag})')
    ax_sf.plane(sf2_strike, sf2_dip, color='teal', linestyle='-', linewidth=1.5, label=f'SF2 ({sf2_notag})')
    ax_sf.plane(gf_strike, gf_dip, color='purple', linestyle='-', linewidth=1.5, label=f'GF ({gf_notag})')

    # Plot Titik Net-Slip (Simbol Bintang Oranye)
    ax_sf.line(netslip_plunge, netslip_trend, marker='*', color='orange', markersize=11, label=f'Net-Slip ({netslip_vec_str})')

    # Plot Vektor Tegasan (Sigma 1, 2, 3)
    ax_sf.line(s1_plunge, s1_trend, 'ro', markersize=9, label=f'σ1 ({s1_vec_str})')
    ax_sf.line(s2_plunge, s2_trend, 'yo', markersize=8, label=f'σ2 ({s2_vec_str})')
    ax_sf.line(s3_plunge, s3_trend, 'go', markersize=8, label=f'σ3 ({s3_vec_str})')

    ax_sf.grid(True, color='gray', alpha=0.5)
    ax_sf.legend(loc='lower left', bbox_to_anchor=(-0.35, -0.38), fontsize='x-small')

    st.pyplot(fig_sf)