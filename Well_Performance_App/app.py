import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go

# --- PAGE CONFIG ---
st.set_page_config(page_title="UTM Well Performance Tool", layout="wide")

st.title("🛢️ Well Production & Choke Performance App")
st.markdown("### Advanced Nodal Analysis: Linear vs Curved IPR")

# --- SIDEBAR INPUTS ---
st.sidebar.header("📁 1. Reservoir Data (IPR)")
pr = st.sidebar.number_input("Reservoir Pressure (Pr), psi", value=3000)
pi = st.sidebar.number_input("Productivity Index (J), STB/D/psi", value=2.0)

st.sidebar.header("📁 2. Tubing & Choke")
depth = st.sidebar.number_input("Well Depth, ft", value=8000)
grad = st.sidebar.number_input("Pressure Gradient, psi/ft", value=0.25, format="%.3f")
s_size = st.sidebar.slider("Choke Size (S), 1/64 inch", 8, 64, 32)
glr = st.sidebar.number_input("GLR, MCF/bbl", value=0.5)

# --- CALCULATION ENGINE ---

# Create rate range for Linear (Max q = Pr * J)
q_linear_max = pr * pi
q_lin = np.linspace(0, q_linear_max, 200)
ipr_linear = pr - (q_lin / pi)

# Create rate range for Vogel (Max q = Pr * J / 1.8)
q_vogel_max = (pi * pr) / 1.8
pwf_vogel_range = np.linspace(0, pr, 200)
q_vogel = q_vogel_max * (1 - 0.2*(pwf_vogel_range/pr) - 0.8*(pwf_vogel_range/pr)**2)

# VLP (Using Vogel rates as base)
thp = (435 * (glr**0.546) * q_vogel) / (s_size**1.89)
vlp_pwf = thp + (grad * depth)

# Find Intersection for the Vogel curve (Most accurate)
idx = np.argmin(np.abs(pwf_vogel_range - vlp_pwf))
op_q = q_vogel[idx]
op_pwf = pwf_vogel_range[idx]

# --- VISUALIZATION ---
fig = go.Figure()

# Add Linear IPR (Straight Line)
fig.add_trace(go.Scatter(x=q_lin, y=ipr_linear, name="Linear IPR (Darcy)", 
                         line=dict(color='lightblue', width=2, dash='dash')))

# Add Curved IPR (Vogel)
fig.add_trace(go.Scatter(x=q_vogel, y=pwf_vogel_range, name="Curved IPR (Vogel)", 
                         line=dict(color='blue', width=4)))

# Add Outflow (VLP)
fig.add_trace(go.Scatter(x=q_vogel, y=vlp_pwf, name="Outflow (VLP + Choke)", 
                         line=dict(color='red', width=4)))

# Operating Point
fig.add_trace(go.Scatter(x=[op_q], y=[op_pwf], name="Operating Point", mode="markers", 
                         marker=dict(size=15, color='black', symbol='cross')))

fig.update_layout(xaxis_title="Rate (q), STB/D", yaxis_title="Pressure, psi", 
                  template="plotly_white", title="Comparison: Darcy vs Vogel IPR")

# --- UI DISPLAY ---
col1, col2 = st.columns([2, 1])
with col1:
    st.plotly_chart(fig, use_container_width=True)
with col2:
    st.success("### System Results")
    st.metric("Operating Flow Rate", f"{op_q:.1f} STB/D")
    st.metric("Flowing BHP (Pwf)", f"{op_pwf:.1f} psi")
    st.divider()
    st.info("""
    **Presentation Note:** 
    The **dashed line** shows the linear Darcy model. 
    The **solid blue curve** is the Vogel model. 
    Notice how Vogel predicts a lower production rate because it accounts for gas interference as pressure drops!
    """)
