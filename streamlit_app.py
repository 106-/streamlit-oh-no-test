import numpy as np
import streamlit as st

HUGE = st.secrets.get("HUGE", False)

if HUGE:
    # float64 × 625,000,000 ≈ 5 GiB → Streamlit Cloud (1GB上限) でOOM
    n = 625_000_000
else:
    n = 1_000

st.write(f"HUGE={HUGE}, allocating n={n:,}")
arr = np.ones(n, dtype=np.float64)
st.write(f"shape={arr.shape}, nbytes={arr.nbytes:,}, sum={arr.sum()}")
