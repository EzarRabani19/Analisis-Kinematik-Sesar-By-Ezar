import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import mplstereonet

# Konfigurasi Halaman
st.set_page_config(
    page_title="Structural Geology & Fault Kinematics (Rickard 1972)", 
    layout="wide",
    page_icon="📐"
)

# Header Aplikasi
st.title("📐 Analisis Kinematik Sesar & Klasifikasi Rickard (1972)")
st.write(
    "Aplikasi khusus geologi struktur untuk penentuan pergerakan sesar "
    "serta determinasi nama sesar berdasarkan klasifikasi deskriptif dan **Rickard (1972)**."
)

st.markdown("---")

# Layout Input dan Output
c_in, c_out = st.columns([1, 1])

with c_in:
    st.subheader("🔍 1. Data Sesar Utama & Gores-Garis")

    f_strike = st.number_input("Strike Sesar Utama (°):", 0.0, 360.0, 45.0, key="f_strike")
    f_dip = st.number_input("Dip Sesar Utama (°):", 0.0, 90.0, 60.0, key="f_dip")
    
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        pitch = st.number_input("Nilai Pitch / Rake (°):", 0.0, 90.0, 30.0, key="pitch_val")
    with col_p2:
        pitch_quadrant = st.selectbox("Arah Pitch dari Strike:", ["Northeast / East", "Northwest / West", "Southwest / West", "Southeast / East"], index=0)

    vertical_sense = st.radio("Sifat Pergerakan Vertikal (Berdasarkan Indikator Sesar):", 
                              ["Naik (Reverse/Thrust)", "Turun (Normal)"], index=0)

    st.markdown("---")
    st.subheader("🔍 2. Pasangan Shear Fracture (SF1 & SF2)")
    
    col_sf1, col_sf2 = st.columns(2)
    with col_sf1:
        st.write("**Shear Fracture 1 (SF1):**")
        sf1_strike = st.number_input("Strike SF1 (°):", 0.0, 360.0, 30.0, key="sf1_str")
        sf1_dip = st.number_input("Dip SF1 (°):", 0.0, 90.0, 70.0, key="sf1_dip")
        
    with col_sf2:
        st.write("**Shear Fracture 2 (SF2):**")
        sf2_strike = st.number_input("Strike SF2 (°):", 0.0, 360.0, 90.0, key="sf2_str")
        sf2_dip = st.number_input("Dip SF2 (°):", 0.0, 90.0, 80.0, key="sf2_dip")

    st.markdown("---")
    st.subheader("🔍 3. Data Gash Fracture (GF)")
    gf_strike = st.number_input("Strike Gash Fracture / GF (°):", 0.0, 360.0, 150.0, key="gf_str")
    gf_dip = st.number_input("Dip Gash Fracture / GF (°):", 0.0, 90.0, 85.0, key="gf_dip")


# ------------------------------------------
# LOGIKA PENENTUAN PERGERAKAN DESKRIPTIF
# ------------------------------------------
if "East" in pitch_quadrant or "North" in pitch_quadrant:
    horiz_label = "Mengiri (Sinistral)"
    is_dextral = False
else:
    horiz_label = "Menganan (Dextral)"
    is_dextral = True

is_reverse = "Naik" in vertical_sense
vert_label = "Naik" if is_reverse else "Turun"

# 1. Penamaan Deskriptif Sederhana
simple_name = f"Sesar {horiz_label.split(' ')[0]} - {vert_label}"

# ------------------------------------------
# LOGIKA KLASIFIKASI RICKARD (1972)
# ------------------------------------------
def get_rickard_classification(dip, pitch, is_rev, is_dex):
    if pitch <= 10:
        return "Right-Slip Fault" if is_dex else "Left-Slip Fault"
    elif pitch >= 80:
        return "Reverse-Slip Fault" if is_rev else "Normal-Slip Fault"
    elif 10 < pitch < 45:
        if is_dex and is_rev:
            return "Right-Reverse Slip Fault"
        elif is_dex and not is_rev:
            return "Right-Normal Slip Fault"
        elif not is_dex and is_rev:
            return "Left-Reverse Slip Fault"
        else:
            return "Left-Normal Slip Fault"
    else:  # 45 <= pitch < 80
        if is_dex and is_rev:
            return "Reverse-Right Slip Fault"
        elif is_dex and not is_rev:
            return "Normal-Right Slip Fault"
        elif not is_dex and is_rev:
            return "Reverse-Left Slip Fault"
        else:
            return "Normal-Left Slip Fault"

rickard_name = get_rickard_classification(f_dip, pitch, is_reverse, is_dextral)

# ------------------------------------------
# KALKULASI VEKTOR TEGASAN (STEREO CONJUGATE & GF)
# ------------------------------------------
# Perpotongan SF1 dan SF2 -> Sumbu Sigma 2 (Neutral / B-Axis)
s2_plunge, s2_trend = mplstereonet.plane_intersection(sf1_strike, sf1_dip, sf2_strike, sf2_dip)

# Vektor Tegasan Utama dari Pole GF:
s1_plunge, s1_trend = mplstereonet.pole(gf_strike, gf_dip)
s3_plunge, s3_trend = mplstereonet.pole((gf_strike + 90) % 360, gf_dip)

# Rejim Tektonik (Anderson, 1951)
if s1_plunge[0] > 60:
    anderson_regime = "Sesar Normal (Normal Faulting Regime)"
elif s1_plunge[0] < 30 and s3_plunge[0] < 30:
    anderson_regime = "Sesar Mendatar (Strike-Slip Faulting Regime)"
else:
    anderson_regime = "Sesar Naik / Anjak (Thrust Faulting Regime)"


# Output di Kolom Kanan
with c_out:
    st.subheader("🎯 Hasil Penamaan Sesar & Kinematik")
    
    # Bagian 1: Penamaan Deskriptif
    st.info(f"### 1. Penamaan Sesar (Deskriptif):\n# **{simple_name}**")
    
    # Bagian 2: Klasifikasi Rickard (1972)
    st.success(f"### 2. Klasifikasi Sesar (Rickard, 1972):\n# **{rickard_name}**")

    st.markdown("---")
    st.write(f"**Rejim Tektonik Utama (Anderson, 1951):** `{anderson_regime}`")

    # Display Vektor Tegasan Utama (Sigma 1, 2, 3)
    col_s1, col_s2, col_s3 = st.columns(3)
    with col_s1:
        st.info(f"**$\sigma_1$ (Kompresi):**\n- Trend: **{s1_trend[0]:.1f}°**\n- Plunge: **{s1_plunge[0]:.1f}°**")
    with col_s2:
        st.warning(f"**$\sigma_2$ (Netral):**\n- Trend: **{s2_trend[0]:.1f}°**\n- Plunge: **{s2_plunge[0]:.1f}°**")
    with col_s3:
        st.error(f"**$\sigma_3$ (Ekstensi):**\n- Trend: **{s3_trend[0]:.1f}°**\n- Plunge: **{s3_plunge[0]:.1f}°**")

    st.markdown("---")
    st.subheader("📊 Stereonet Wulff Net")

    fig_sf, ax_sf = plt.subplots(figsize=(5.5, 5.5), subplot_kw={'projection': 'stereonet'})

    # Plot Bidang Sesar, Pasangan SF, dan GF
    ax_sf.plane(f_strike, f_dip, 'b-', linewidth=2.5, label=f'Sesar Utama ({f_strike:.0f}°/{f_dip:.0f}°)')
    ax_sf.plane(sf1_strike, sf1_dip, 'g--', linewidth=1.5, label=f'SF1 ({sf1_strike:.0f}°/{sf1_dip:.0f}°)')
    ax_sf.plane(sf2_strike, sf2_dip, 'c--', linewidth=1.5, label=f'SF2 ({sf2_strike:.0f}°/{sf2_dip:.0f}°)')
    ax_sf.plane(gf_strike, gf_dip, 'r-.', linewidth=1.5, label=f'GF ({gf_strike:.0f}°/{gf_dip:.0f}°)')

    # Plot Vektor Tegasan
    ax_sf.line(s1_plunge, s1_trend, 'ro', markersize=9, label=f'σ1 ({s1_trend[0]:.0f}°/{s1_plunge[0]:.0f}°)')
    ax_sf.line(s2_plunge, s2_trend, 'yo', markersize=8, label=f'σ2 ({s2_trend[0]:.0f}°/{s2_plunge[0]:.0f}°)')
    ax_sf.line(s3_plunge, s3_trend, 'go', markersize=8, label=f'σ3 ({s3_trend[0]:.0f}°/{s3_plunge[0]:.0f}°)')

    ax_sf.grid(True, color='gray', alpha=0.5)
    ax_sf.legend(loc='lower left', bbox_to_anchor=(-0.25, -0.25), fontsize='x-small')

    st.pyplot(fig_sf)