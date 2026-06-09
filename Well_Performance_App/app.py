import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="UTM Well Nodal Analysis", layout="wide", page_icon="🛢️")

# --- HEADER & BRANDING ---
st.title("🛢️ Well Production & Choke Performance App")
st.markdown("""
**Course:** Petroleum & Chemical Engineering Calculations  
**Project:** Option A - Well Production Performance  
**Logic:** Integrated Nodal Analysis (Reservoir + Tubing + Choke)  
*Based on the syllabus of Dr. Abdul Rahim Risal*
""")

# --- SIDEBAR INPUTS (Dynamic User Data) ---
st.sidebar.header("📁 1. Reservoir Data (IPR)")
pr = st.sidebar.number_input("Reservoir Pressure (Pr), psi", value=3000, help="Static reservoir pressure")
pi = st.sidebar.number_input("Productivity Index (J), STB/D/psi", value=2.0, help="Inflow ability")

st.sidebar.header("📁 2. Wellbore & Choke (Outflow)")
depth = st.sidebar.number_input("Well Depth (TVD), ft", value=8000)
grad = st.sidebar.number_input("Fluid Pressure Gradient, psi/ft", value=0.25, format="%.3f")

st.sidebar.subheader("Choke Settings (Slide 8)")
# Gilbert Correlation Constants: A=435, B=0.546, C=1.89
S = st.sidebar.slider("Choke Size (S), 1/64 inch", 8, 64, 32)
glr = st.sidebar.number_input("Gas-Liquid Ratio (GLR), MCF/bbl", value=0.5)

# --- CALCULATION ENGINE ---
# Create a range of flow rates
q = np.linspace(1, pr * pi, 200)

# 1. IPR Calculation: Pwf = Pr - (q/J)
ipr_pwf = pr - (q / pi)

# 2. Choke Performance (Gilbert Correlation - Slide 8)
# Formula: THP = (A * GLR^B * q) / S^C
thp = (435 * (glr**0.546) * q) / (S**1.89)

# 3. VLP Calculation: Pwf = THP + (Grad * Depth)
vlp_pwf = thp + (grad * depth)

# 4. Find Intersection (Operating Point)
# We find where the difference between Inflow and Outflow is minimal
idx = np.argmin(np.abs(ipr_pwf - vlp_pwf))
op_q = q[idx]
op_pwf = ipr_pwf[idx]
op_thp = thp[idx]

# --- VISUALIZATION ---
fig = go.Figure()

# Add IPR Line (Blue)
fig.add_trace(go.Scatter(x=q, y=ipr_pwf, name="IPR (Reservoir)", 
                         line=dict(color='#1f77b4', width=4)))

# Add VLP Line (Red)
fig.add_trace(go.Scatter(x=q, y=vlp_pwf, name="VLP (Well + Choke)", 
                         line=dict(color='#d62728', width=4)))

# Add Choke THP Line (Green Dash)
fig.add_trace(go.Scatter(x=q, y=thp, name="Surface Choke THP", 
                         line=dict(color='#2ca02c', dash='dash')))

# Add Operating Point Marker
fig.add_trace(go.Scatter(x=[op_q], y=[op_pwf], name="Operating Point",
                         mode="markers", marker=dict(size=15, color='black', symbol='cross')))

fig.update_layout(
    title="Nodal Analysis: Inflow vs Outflow Intersection",
    xaxis_title="Production Rate (q), STB/D",
    yaxis_title="Pressure (P), psi",
    yaxis_range=[0, pr + 500],
    template="plotly_white",
    legend=dict(yanchor="top", y=0.99, xanchor="right", x=0.99),
    hovermode="x unified"
)

# --- UI LAYOUT ---
col_graph, col_res = st.columns([2, 1])

with col_graph:
    st.plotly_chart(fig, use_container_width=True)

with col_res:
    st.success("### 🎯 System Analysis")
    st.metric("Operating Flow Rate", f"{op_q:.1f} STB/D")
    st.metric("Flowing BHP (Pwf)", f"{op_pwf:.1f} psi")
    st.metric("Surface Pressure (THP)", f"{op_thp:.1f} psi")
    
    st.divider()
    st.info(f"""
    **Current Choke Size:** {S}/64"  
    **Engineering Conclusion:**  
    The well stabilizes at **{op_q:.1f} STB/D**. 
    Adjust the Choke Size in the sidebar to see how the operating point moves along the IPR curve.
    """)

# Data Expander
with st.expander("📊 View Detailed Calculation Data"):
    df = pd.DataFrame({
        "Flow Rate (q)": q,
        "IPR Pwf (psi)": ipr_pwf,
        "VLP Pwf (psi)": vlp_pwf,
        "Surface THP (psi)": thp
    }).round(2)
    st.dataframe(df, use_container_width=True)