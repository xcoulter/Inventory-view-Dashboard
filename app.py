
import streamlit as st
import pandas as pd

def load_data(uploaded_file):
    df = pd.read_csv(uploaded_file)
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    df['month'] = df['timestamp'].dt.to_period('M')
    df = df[df['status'] == 'complete']
    return df

def main():
    st.set_page_config(page_title="Monthly Actions Report", layout="wide")
    st.title("📊 Monthly Actions Summary")

    uploaded_file = st.sidebar.file_uploader("Upload Actions Report CSV", type="csv")

    if uploaded_file is None:
        st.info("Please upload an actions report CSV to get started.")
        return

    df = load_data(uploaded_file)

    # Sidebar Filters
    st.sidebar.header("🔍 Filters")
    months = sorted(df['month'].dropna().unique())
    assets = sorted(df['asset'].dropna().unique())
    inventories = sorted(df['inventory'].dropna().unique())

    selected_month = st.sidebar.selectbox("Select Month", months)
    selected_asset = st.sidebar.selectbox("Select Asset", ["All"] + assets)
    selected_inventory = st.sidebar.selectbox("Select Inventory", ["All"] + inventories)

    # Filter dataset
    filtered = df[df['month'] == selected_month]
    if selected_asset != "All":
        filtered = filtered[filtered['asset'] == selected_asset]
    if selected_inventory != "All":
        filtered = filtered[filtered['inventory'] == selected_inventory]

    # Aggregation
    ending_balance_summary = (
        filtered.groupby(['month', 'asset'])['assetBalance']
        .last()
        .reset_index(name='ending_balance')
    )

    gain_loss_summary = (
        filtered.groupby(['month', 'asset', 'inventory'])[['shortTermGainLoss', 'longTermGainLoss']]
        .sum()
        .reset_index()
    )

    combined = pd.merge(
        gain_loss_summary,
        ending_balance_summary,
        on=['month', 'asset'],
        how='left'
    )

    # Summary Metrics
    total_st = combined['shortTermGainLoss'].sum()
    total_lt = combined['longTermGainLoss'].sum()
    st.subheader(f"Summary for {selected_month}")
    col1, col2 = st.columns(2)
    col1.metric("Short-Term Gain/Loss", f"${total_st:,.2f}")
    col2.metric("Long-Term Gain/Loss", f"${total_lt:,.2f}")

    st.markdown("---")
    st.subheader("📁 Per Asset & Inventory Details")
    with st.expander("Click to view detailed table"):
        st.dataframe(combined)

if __name__ == "__main__":
    main()
