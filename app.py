import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# --- Page setup ---
st.set_page_config(page_title="Environmental Data Dashboard", layout="wide")
st.title("🌿 Environmental Data Dashboard")

# --- Sidebar controls ---
st.sidebar.header("⚙️ Controls")
file = st.sidebar.file_uploader("📂 Upload your .txt or .csv file (comma separated)", type=["txt", "csv"])

if file is not None:
    # --- Read file after 'BEGIN RECORD' ---
    lines = file.readlines()
    file.seek(0)
    start_index = next((i + 1 for i, l in enumerate(lines) if b"BEGIN RECORD" in l), 0)
    df = pd.read_csv(file, skiprows=start_index, sep=",", on_bad_lines="skip")

    # --- Clean empty or SDI rows ---
    df = df.dropna(how="all")
    df = df[~df.astype(str).apply(lambda x: x.str.contains("SDI", case=False, na=False)).any(axis=1)]

    # --- Detect datetime column ---
    date_cols = [c for c in df.columns if "date" in c.lower() or "time" in c.lower()]
    if date_cols:
        date_col = date_cols[0]
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        df = df.sort_values(date_col)
        st.sidebar.success(f"Using datetime column: {date_col}")
    else:
        st.warning("⚠️ No datetime column detected.")
        date_col = None

    # --- Sidebar variable selectors ---
    num_cols = df.select_dtypes(include="number").columns.tolist()
    var1 = st.sidebar.selectbox("Variable for Plot 1 (Time Series)", num_cols, index=0 if num_cols else None)
    var2 = st.sidebar.selectbox("Variable for Plot 2 (Boxplot)", num_cols, index=1 if len(num_cols) > 1 else 0)

    # --- Tabs ---
    tab1, tab2 = st.tabs(["📋 Data", "📊 Charts"])

    # --- Tab 1: Data + Stats ---
    with tab1:
        st.subheader("Data Preview")
        st.dataframe(df, use_container_width=True, height=500)
        st.markdown(f"**Rows:** {df.shape[0]} | **Columns:** {df.shape[1]}")
        st.subheader("Descriptive Statistics")
        st.write(df.describe(include="all"))

    # --- Tab 2: Charts ---
    with tab2:
        if date_col and var1 in df.columns:
            st.subheader(f"📈 {var1} over time with ±1 Std. Dev.")

            # Rolling window and smoothing options
            window = st.sidebar.slider("Rolling window size", 5, 200, 30)
            df["mean"] = df[var1].rolling(window=window, center=True).mean()
            df["std"] = df[var1].rolling(window=window, center=True).std()

            # Fill NaN edges to keep band continuous
            df["mean"] = df["mean"].fillna(method='bfill').fillna(method='ffill')
            df["std"] = df["std"].fillna(method='bfill').fillna(method='ffill')

            # Calculate upper and lower bounds
            df["upper"] = df["mean"] + df["std"]
            df["lower"] = df["mean"] - df["std"]

            # --- Plot with filled standard deviation area ---
            fig = go.Figure()

            # Shaded ±1 std area (smooth, continuous)
            fig.add_trace(go.Scatter(
                x=pd.concat([df[date_col], df[date_col][::-1]]),
                y=pd.concat([df["upper"], df["lower"][::-1]]),
                fill='toself',
                fillcolor='rgba(0, 123, 255, 0.2)',
                line=dict(color='rgba(255,255,255,0)'),
                hoverinfo="skip",
                showlegend=True,
                name='±1 Std. Dev.'
            ))

            # Main line
            fig.add_trace(go.Scatter(
                x=df[date_col],
                y=df[var1],
                mode='lines+markers',
                name=var1,
                line=dict(color='rgba(0, 123, 255, 1)', width=2)
            ))

            fig.update_layout(
                title=f"{var1} over time with ±1 Std. Dev. (window={window})",
                xaxis_title=date_col,
                yaxis_title=var1,
                template="plotly_white"
            )

            st.plotly_chart(fig, use_container_width=True)

        if var2 in df.columns:
            st.subheader(f"📦 Distribution of {var2}")
            fig2 = px.box(df, y=var2, title=f"Boxplot of {var2}", points="outliers", template="plotly_white")
            st.plotly_chart(fig2, use_container_width=True)

else:
    st.info("👈 Upload a comma-separated .txt or .csv file from the sidebar to begin.")
