import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go

# --- PAGE CONFIG ---
st.set_page_config(page_title="UTM Well Performance Tool", layout="wide")

# --- HEADER ---
st.title("🛢️ Well Production & Choke Performance App")
st.markdown("### Comparison: Linear (Darcy) vs Curved (Vogel) IPR")
st.write("Calculations based on Dr. Abdul Rahim Risal's Chapter 2 syllabus.")

# --- SIDEBAR INPUTS ---
st.sidebar.header("📁 1. Reservoir Data (IPR)")
pr = st.sidebar.number_input("Reservoir Pressure (Pr), psi", value=3000)
pi = st.sidebar.number_input("Productivity Index (J), STB/D/psi", value=2.0)

st.sidebar.header("📁 2. Outflow Data (VLP & Choke)")
depth = st.sidebar.number_input("Well Depth, ft", value=8000)
grad = st.sidebar.number_input("Pressure Gradient, psi/ft", value=0.25, format="%.3f")
s_size = st.sidebar.slider("Choke Size (S), 1/64 inch", 8, 64, 32)
glr = st.sidebar.number_input("GLR, MCF/bbl", value=0.5)

# --- CALCULATION ENGINE ---

# A. Inflow Calculations
# 1. Linear (Darcy)
q_linear_max = pr * pi
q_lin = np.linspace(0, q_linear_max, 200)
ipr_linear = pr - (q_lin / pi)

# 2. Curved (Vogel)
q_vogel_max = (pi * pr) / 1.8
pwf_vogel_range = np.linspace(0, pr, 200)
q_vogel = q_vogel_max * (1 - 0.2*(pwf_vogel_range/pr) - 0.8*(pwf_vogel_range/pr)**2)

# B. Outflow Calculations (VLP)
# Using Gilbert Correlation for Choke THP (Slide 8)
# Formula: THP = (435 * GLR^0.546 * q) / S^1.89
thp = (435 * (glr**0.546) * q_vogel) / (s_size**1.89)
vlp_pwf = thp + (grad * depth)

# C. Find Intersection for Vogel (The Operating Point)
idx = np.argmin(np.abs(pwf_vogel_range - vlp_pwf))
op_q = q_vogel[idx]
op_pwf = pwf_vogel_range[idx]
op_thp = thp[idx]

# --- UI LAYOUT (Tabs) ---
tab1, tab2 = st.tabs(["📈 Nodal Analysis Graph", "🧮 Calculation Workings"])

with tab1:
    col_graph, col_res = st.columns([2, 1])
    
    with col_graph:
        fig = go.Figure()
        # Add Darcy Line
        fig.add_trace(go.Scatter(x=q_lin, y=ipr_linear, name="Linear IPR (Darcy)", 
                                 line=dict(color='lightblue', width=2, dash='dash')))
        # Add Vogel Curve
        fig.add_trace(go.Scatter(x=q_vogel, y=pwf_vogel_range, name="Curved IPR (Vogel)", 
                                 line=dict(color='blue', width=4)))
        # Add VLP
        fig.add_trace(go.Scatter(x=q_vogel, y=vlp_pwf, name="Outflow (VLP + Choke)", 
                                 line=dict(color='red', width=4)))
        # Operating Point
        fig.add_trace(go.Scatter(x=[op_q], y=[op_pwf], name="Operating Point", mode="markers", 
                                 marker=dict(size=15, color='black', symbol='cross')))

        fig.update_layout(xaxis_title="Rate (q), STB/D", yaxis_title="Pressure, psi", 
                          template="plotly_white", title="Darcy vs Vogel IPR Comparison")
        st.plotly_chart(fig, use_container_width=True)

    with col_res:
        st.success("### System Results")
        st.metric("Operating Flow Rate", f"{op_q:.1f} STB/D")
        st.metric("Flowing BHP (Pwf)", f"{op_pwf:.1f} psi")
        st.metric("Surface THP", f"{op_thp:.1f} psi")
        st.divider()
        st.info("""
        **Observation:** The dashed line is the Darcy model. The solid blue curve is the Vogel model. 
        Vogel is more realistic for wells producing below bubble point.
        """)

with tab2:
    st.subheader("Step-by-Step Engineering Formulas")
    
    st.markdown("#### 1. Inflow Performance (IPR)")
    col_a, col_b = st.columns(2)
    with col_a:
        st.write("**Linear Darcy Model:**")
        st.latex(r"P_{wf} = P_r - \frac{q}{J}")
    with col_b:
        st.write("**Vogel Curved Model:**")
        st.latex(r"q = q_{max} \left[ 1 - 0.2 \left( \frac{P_{wf}}{P_r} \right) - 0.8 \left( \frac{P_{wf}}{P_r} \right)^2 \right]")
    
    st.markdown("#### 2. Surface Choke Performance (Gilbert)")
    st.latex(r"P_{wh} (THP) = \frac{A \cdot GLR^B \cdot q}{S^C}")
    st.write(f"Using Gilbert's constants: A=435, B=0.546, C=1.89 (Slide 8)")
    
    st.markdown("#### 3. Total Outflow (VLP)")
    st.latex(r"P_{wf} = THP + (Grad \cdot Depth)")
    
    st.divider()
    st.subheader("Values at Operating Point")
    st.write(f"- At a rate of **{op_q:.1f} STB/D**, the pressure required at the surface is **{op_thp:.2f} psi**.")
    st.write(f"- The pressure drop in the **{depth} ft** tubing is **{grad * depth:.1f} psi**.")
    st.write(f"- Therefore, the required Bottomhole Pressure (Pwf) is **{op_pwf:.1f} psi**.")

    with st.expander("📊 View Full Calculation Table"):
        df = pd.DataFrame({
            "Flow Rate (q)": q_vogel[::10],
            "Vogel IPR (psi)": pwf_vogel_range[::10],
            "Choke THP (psi)": thp[::10],
            "VLP Pwf (psi)": vlp_pwf[::10]
        }).round(2)
        st.table(df)
