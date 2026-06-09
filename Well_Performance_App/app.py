import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go

# --- PAGE CONFIG ---
st.set_page_config(page_title="UTM Well Nodal App", layout="wide")

st.title("🛢️ UTM Well Production & Choke Performance")
st.markdown("Developed by: **Your Group Name** | Logic: Vogel IPR + Slip/No-Slip VLP")

# --- SIDEBAR INPUTS ---
st.sidebar.header("📁 Reservoir Data (IPR)")
pr = st.sidebar.number_input("Reservoir Pressure (Pr), psi", value=3000)
pi = st.sidebar.number_input("Productivity Index (J)", value=2.0)

st.sidebar.header("📁 Outflow Data (VLP & Choke)")
depth = st.sidebar.number_input("Well Depth, ft", value=8000)
s_size = st.sidebar.slider("Choke Size (S), 1/64 inch", 8, 64, 32)
glr = st.sidebar.number_input("GLR, MCF/bbl", value=0.5)

# --- CALCULATION ENGINE ---
q_vogel_max = (pi * pr) / 1.8
pwf_vogel_range = np.linspace(1, pr, 200)
q_ipr = q_vogel_max * (1 - 0.2*(pwf_vogel_range/pr) - 0.8*(pwf_vogel_range/pr)**2)

# VLP Components (Logic from Slide 27-28)
thp = (435 * (glr**0.546) * q_ipr) / (s_size**1.89)
friction = 0.00005 * (q_ipr**1.8) 
loading = 5000 / (q_ipr + 10) # Liquid Loading effect near origin

vlp_slip = thp + (0.35 * depth) + friction + loading
vlp_noslip = thp + (0.25 * depth) + friction + loading

# Find Intersection
idx = np.argmin(np.abs(pwf_vogel_range - vlp_slip))
op_q = q_ipr[idx]
op_pwf = pwf_vogel_range[idx]
op_thp = thp[idx]

# --- UI LAYOUT (Tabs) ---
tab1, tab2 = st.tabs(["📈 Performance Curves", "🧮 Calculation Workings"])

with tab1:
    col1, col2 = st.columns([2, 1])
    with col1:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=q_ipr, y=pwf_vogel_range, name="IPR (Vogel Curve)", line=dict(color='blue', width=4)))
        fig.add_trace(go.Scatter(x=q_ipr, y=vlp_slip, name="VLP: Slip (Heavier)", line=dict(color='red', width=3)))
        fig.add_trace(go.Scatter(x=q_ipr, y=vlp_noslip, name="VLP: No-Slip (Lighter)", line=dict(color='orange', width=2, dash='dot')))
        fig.add_trace(go.Scatter(x=[op_q], y=[op_pwf], name="Operating Point", mode="markers", marker=dict(size=15, color='black', symbol='cross')))
        fig.update_layout(xaxis_title="Rate (q), STB/D", yaxis_title="Pressure, psi", template="plotly_white", height=600)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.success("### Operating Point")
        st.metric("Production Rate (q)", f"{op_q:.1f} STB/D")
        st.metric("Bottomhole Pressure (Pwf)", f"{op_pwf:.1f} psi")
        st.metric("Surface Pressure (THP)", f"{op_thp:.1f} psi")
        st.info("**Analysis:** The intersection shows the equilibrium point where the reservoir delivery matches the total wellbore and choke pressure requirements.")

with tab2:
    st.subheader("Step-by-Step Engineering Formulas")
    
    st.markdown("#### 1. Inflow Performance (Vogel Equation)")
    st.latex(r"q = q_{max} \left[ 1 - 0.2 \left( \frac{P_{wf}}{P_r} \right) - 0.8 \left( \frac{P_{wf}}{P_r} \right)^2 \right]")
    st.write(f"Based on your inputs, the theoretical maximum flow ($q_{{max}}$) is **{q_vogel_max:.1f} STB/D**.")

    st.markdown("#### 2. Outflow Performance (VLP)")
    st.latex(r"P_{wf} = P_{wh} + \Delta P_{gravity} + \Delta P_{friction} + \Delta P_{loading}")
    st.write("- **Gravity (Slip):** 0.35 psi/ft used for heavier multi-phase column.")
    st.write("- **Gravity (No-Slip):** 0.25 psi/ft used for ideal homogeneous flow.")

    st.markdown("#### 3. Surface Choke Performance (Gilbert Correlation)")
    st.latex(r"P_{wh} (THP) = \frac{435 \cdot GLR^{0.546} \cdot q}{S^{1.89}}")
    st.write(f"At the operating point, the Choke creates a back-pressure of **{op_thp:.2f} psi**.")
    
    st.divider()
    st.write("#### 📊 Intermediate Data Table")
    calc_df = pd.DataFrame({
        "Flow Rate (q)": q_ipr[::20],
        "Choke THP": thp[::20],
        "VLP (Slip)": vlp_slip[::20],
        "VLP (No-Slip)": vlp_noslip[::20]
    }).round(2)
    st.table(calc_df)
