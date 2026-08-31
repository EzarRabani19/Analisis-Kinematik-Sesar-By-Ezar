import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import mplstereonet

# Konfigurasi Halaman
st.set_page_config(
    page_title="Structural Geology & Fault Kinematics", 
    layout="wide",
    page_icon="📐"
)

# ---------------------------------------------------------
# HELPER VEKTOR & KLASIFIKASI RICKARD (1972)
# ---------------------------------------------------------

def format_geology_notation(strike, dip):
    strike = strike % 360
    ddir = (strike + 90) % 360
    dirs = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    cardinal = dirs[int(round(ddir / 45.0)) % 8]
    return f"N {strike:.0f}° E / {dip:.0f}° {cardinal}"

def format_vector_notation(plunge, trend):
    return f"{float(plunge):.0f}° / N {float(trend):.0f}° E"

def plane_to_normal(strike, dip):
    s_rad = np.radians(strike)
    d_rad = np.radians(dip)
    nx = np.sin(d_rad) * np.cos(s_rad)
    ny = -np.sin(d_rad) * np.sin(s_rad)
    nz = np.cos(d_rad)
    vec = np.array([nx, ny, nz])
    return vec / np.linalg.norm(vec)

def vec_to_plunge_trend(vec):
    vec = vec / np.linalg.norm(vec)
    if vec[2] > 0:
        vec = -vec
    plunge = np.degrees(np.arcsin(-vec[2]))
    trend = np.degrees(np.arctan2(vec[0], vec[1])) % 360
    return float(plunge), float(trend), vec

def pole_to_plane(plunge, trend):
    strike = (trend - 90) % 360
    dip = 90.0 - plunge
    if dip < 0:
        dip = abs(dip)
        strike = (strike + 180) % 360
    return float(strike), float(dip)

# HITUNG PITCH GEOMETRIS
def calculate_pitch(f_strike, f_dip, net_trend, net_plunge):
    d_dip = np.radians(f_dip)
    pitch_rad = np.arctan2(np.tan(np.radians(net_plunge)), np.sin(d_dip))
    pitch = np.degrees(pitch_rad) % 180
    return float(pitch)

# KLASIFIKASI RICKARD (1972)
def get_rickard_classification(dip, pitch, is_dextral, is_reverse):
    sense = "Right" if is_dextral else "Left"
    type_str = "Reverse" if is_reverse else "Normal"
    
    dip_cat = "Low Dip" if dip < 45 else "High Dip"
        
    if pitch <= 15:
        return f"{sense} Lateral Strike-Slip Fault"
    elif pitch <= 45:
        return f"{sense} Normal/Reverse {type_str} Slip Fault ({dip_cat})" if not is_reverse else f"{sense} Thrust Slip Fault"
    elif pitch <= 75:
        return f"{sense} {type_str} Oblique Slip Fault"
    else:
        return f"Pure {type_str} Slip Fault"


# Header Aplikasi
st.title("Analisis Kinematik Sesar By Ezar Rabani")
st.write(
    "Visualisasi Schmidt Net presisi tinggi berbasis aljabar vektor murni & klasifikasi Rickard:\n"
    "- **$\sigma_2$**: Perpotongan SF1 $\\times$ SF2\n"
    "- **Bidang Bantu**: Bidang tegak lurus $\sigma_2$\n"
    "- **Net-Slip**: Perpotongan Bidang Bantu $\\times$ Sesar Utama\n"
    "- **$\sigma_1$**: Perpotongan Bidang Bantu $\\times$ GF\n"
    "- **$\sigma_3$**: Titik $90^\circ$ dari $\sigma_1$ di sepanjang Bidang Bantu"
)

st.markdown("---")

c_in, c_out = st.columns([1, 1])

with c_in:
    st.subheader("1. Data Sesar Utama & Pitch")
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        f_strike = st.number_input("Strike Sesar Utama (°):", 0.0, 360.0, 45.0, step=1.0, key="f_strike")
    with col_f2:
        f_dip = st.number_input("Dip Sesar Utama (°):", 0.0, 90.0, 60.0, step=1.0, key="f_dip")
        
    use_manual_pitch = st.checkbox("Gunakan Input Pitch Manual (Gores-Garis Lapangan)", value=False)
    if use_manual_pitch:
        manual_pitch = st.number_input("Pitch / Rake Net-Slip (°):", 0.0, 90.0, 45.0, step=1.0, key="m_pitch")
    else:
        manual_pitch = None

    st.caption(f"Sesar Utama: **{format_geology_notation(f_strike, f_dip)}**")

    st.markdown("---")
    st.subheader("2. Pasangan Shear Fracture (SF1 & SF2)")
    col_sf1, col_sf2 = st.columns(2)
    with col_sf1:
        sf1_strike = st.number_input("Strike SF1 (°):", 0.0, 360.0, 30.0, step=1.0, key="sf1_str")
        sf1_dip = st.number_input("Dip SF1 (°):", 0.0, 90.0, 70.0, step=1.0, key="sf1_dip")
        st.caption(f"SF1: **{format_geology_notation(sf1_strike, sf1_dip)}**")
        
    with col_sf2:
        sf2_strike = st.number_input("Strike SF2 (°):", 0.0, 360.0, 110.0, step=1.0, key="sf2_str")
        sf2_dip = st.number_input("Dip SF2 (°):", 0.0, 90.0, 80.0, step=1.0, key="sf2_dip")
        st.caption(f"SF2: **{format_geology_notation(sf2_strike, sf2_dip)}**")

    st.markdown("---")
    st.subheader("3. Data Gash Fracture (GF)")
    gf_strike = st.number_input("Strike GF (°):", 0.0, 360.0, 150.0, step=1.0, key="gf_str")
    gf_dip = st.number_input("Dip GF (°):", 0.0, 90.0, 85.0, step=1.0, key="gf_dip")
    st.caption(f"GF: **{format_geology_notation(gf_strike, gf_dip)}**")


# ---------------------------------------------------------
# KALKULASI INTERSEKSI VEKTOR GEOMETRI
# ---------------------------------------------------------

n_f = plane_to_normal(f_strike, f_dip)
n_sf1 = plane_to_normal(sf1_strike, sf1_dip)
n_sf2 = plane_to_normal(sf2_strike, sf2_dip)
n_gf = plane_to_normal(gf_strike, gf_dip)

# 1. SIGMA 2
v_s2_raw = np.cross(n_sf1, n_sf2)
s2_plunge, s2_trend, v_s2 = vec_to_plunge_trend(v_s2_raw)

# 2. BIDANG BANTU
aux_strike, aux_dip = pole_to_plane(s2_plunge, s2_trend)
n_aux = plane_to_normal(aux_strike, aux_dip)

# 3. NET-SLIP
v_net_raw = np.cross(n_aux, n_f)
netslip_plunge, netslip_trend, _ = vec_to_plunge_trend(v_net_raw)

# 4. SIGMA 1
v_s1_raw = np.cross(n_aux, n_gf)
s1_plunge, s1_trend, v_s1 = vec_to_plunge_trend(v_s1_raw)

# 5. SIGMA 3
v_s3_raw = np.cross(n_aux, v_s1)
s3_plunge, s3_trend, _ = vec_to_plunge_trend(v_s3_raw)

# 6. PENENTUAN PITCH & RICKARD CLASSIFICATION
calc_pitch = calculate_pitch(f_strike, f_dip, netslip_trend, netslip_plunge)
final_pitch = manual_pitch if use_manual_pitch else calc_pitch

strike_diff = (f_strike - s1_trend) % 180
is_dextral = 0 < strike_diff < 90
is_reverse = s1_plunge < s3_plunge

horiz_str = "Menganan (Dextral)" if is_dextral else "Mengiri (Sinistral)"
vert_str = "Naik" if is_reverse else "Turun"

rickard_name = get_rickard_classification(f_dip, final_pitch, is_dextral, is_reverse)


# Output Display
with c_out:
    st.subheader("Hasil Kinematik & Klasifikasi Rickard (1972)")
    
    st.success(f"### Klasifikasi Rickard (1972):\n# **{rickard_name}**")
    st.info(f"**Sifat Pergerakan:** Sesar {horiz_str.split(' ')[0]} - {vert_str}\n\n📌 **Pitch Net-Slip Digunakan:** `{final_pitch:.1f}°` " + (f"*(Manual)*" if use_manual_pitch else f"*(Kalkulasi Geometri: {calc_pitch:.1f}°)*"))

    col_s1, col_s2, col_s3 = st.columns(3)
    with col_s1:
        st.info(f"**$\sigma_1$ (Bantu $\\times$ GF):**\n{format_vector_notation(s1_plunge, s1_trend)}")
    with col_s2:
        st.warning(f"**$\sigma_2$ (SF1 $\\times$ SF2):**\n{format_vector_notation(s2_plunge, s2_trend)}")
    with col_s3:
        st.error(f"**$\sigma_3$ ($90^\circ$ di Bantu):**\n{format_vector_notation(s3_plunge, s3_trend)}")

    st.markdown(f"**Bidang Bantu:** `{format_geology_notation(aux_strike, aux_dip)}`")
    st.markdown(f"**Vektor Net-Slip (Bantu $\\times$ Sesar):** `{format_vector_notation(netslip_plunge, netslip_trend)}`")

    st.markdown("---")
    st.subheader("Stereonet Schmidt Net (Equal Area)")

    fig_sf, ax_sf = plt.subplots(figsize=(6, 6), subplot_kw={'projection': 'equal_area_stereonet'})

    # Plot Bidang (Great Circles)
    ax_sf.plane(f_strike, f_dip, color='red', linewidth=2.0, label='Sesar Utama')
    ax_sf.plane(aux_strike, aux_dip, color='blue', linewidth=2.0, linestyle='--', label='Bidang Bantu')
    ax_sf.plane(sf1_strike, sf1_dip, color='green', linewidth=1.2, label='SF1')
    ax_sf.plane(sf2_strike, sf2_dip, color='teal', linewidth=1.2, label='SF2')
    ax_sf.plane(gf_strike, gf_dip, color='purple', linewidth=1.2, label='GF')

    # Plot Titik Hasil Interseksi Geometri
    ax_sf.line(netslip_plunge, netslip_trend, '^', color='black', markeredgecolor='red', markersize=11, label='Net-Slip (Bantu x Sesar)')
    ax_sf.line(s1_plunge, s1_trend, 'ro', markersize=9, label=f'σ1 ({format_vector_notation(s1_plunge, s1_trend)})')
    ax_sf.line(s2_plunge, s2_trend, 'yo', markersize=9, label=f'σ2 ({format_vector_notation(s2_plunge, s2_trend)})')
    ax_sf.line(s3_plunge, s3_trend, 'go', markersize=9, label=f'σ3 ({format_vector_notation(s3_plunge, s3_trend)})')

    ax_sf.grid(True, color='gray', alpha=0.5)
    ax_sf.legend(loc='lower left', bbox_to_anchor=(-0.35, -0.38), fontsize='x-small')

    st.pyplot(fig_sf)