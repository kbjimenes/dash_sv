import streamlit as st
import pandas as pd
import numpy as np

st.title("Mi primer dashboard con Streamlit")

# Crear un DataFrame de ejemplo
df = pd.DataFrame(
    np.random.randn(10, 3),
    columns=['A', 'B', 'C']
)

st.write("Aquí tienes una tabla con datos aleatorios:")
st.dataframe(df)

st.line_chart(df)
