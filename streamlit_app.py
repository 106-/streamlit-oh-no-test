import numpy as np
import streamlit as st

st.write("allocating ~5 GiB...")

# float64 (8 bytes) × 625,000,000 = 5,000,000,000 bytes ≈ 5 GiB
arr = np.ones(625_000_000, dtype=np.float64)

st.write(f"shape={arr.shape}, nbytes={arr.nbytes:,}")
st.write(f"sum={arr.sum()}")
