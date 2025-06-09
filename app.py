import streamlit as st
import pandas as pd
import pytz


def load_data(uploaded_file, selected_timezone):
    df = pd.read_csv(uploaded_file)
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce', utc=True)

    # Convert to selected timezone
    try:
        df['timestamp'] = df['timestamp'].dt.tz_convert(selected_timezone)
    except Exception:
        st.warning("Timezone conversion failed. Showing timestamps in UTC.")

    df['month'] = df['timestamp'].dt.to_period('M')
    df = df[df['status'] == 'complete']

    # Handle missing inventory column or values
    if 'inventory' not in df.columns:
        df['inventory'] = 'Unspecified'
    else:
        df['inventory'] = df['inventory'].fillna('Unspecified')

    return df


def main():
    st.set_page_config(page_title="Monthly Actions Report", layout="wide")
    st.title("📊 Monthly Actions Summary")

    uploaded_file = st.sidebar.file_uploader("Upload Actions Report CSV", type="csv")

    # Timezone selection
    st.sidebar.markdown("---")
    st.sidebar.subheader("🕒 Timezone")
    timezones = pytz.all_timezones
    selected_timezone = st.sidebar.selectbox("Select your timezone", ["UTC"] + timezones, index=0)

    if uploaded_file is None:
        st.info("Please upload an actions report CSV to get started.")
        return

    df = load_data(uploaded_file, selected_timezone)

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
    latest_balance = (
        filtered.sort_values('timestamp')
        .groupby(['month', 'asset', 'inventory'], as_index=False)
        .last()[['month', 'asset', 'inventory', 'assetBalance']]
        .rename(columns={'assetBalance': 'ending_balance'})
    )

    agg_fields = ['shortTermGainLoss', 'longTermGainLoss']
    include_impairment_expense = 'impairmentExpense' in df.columns
    include_impairment_reversal = 'impairmentReversal' in df.columns

    if include_impairment_expense:
        agg_fields.append('impairmentExpense')
    if include_impairment_reversal:
        agg_fields.append('impairmentReversal')

    gain_loss_summary = (
        filtered.groupby(['month', 'asset', 'inventory'])[agg_fields]
        .sum()
        .reset_index()
    )

    combined = pd.merge(
        gain_loss_summary,
        latest_balance,
        on=['month', 'asset', 'inventory'],
        how='left'
    )

    # Summary Metrics
    total_st = combined['shortTermGainLoss'].sum()
    total_lt = combined['longTermGainLoss'].sum()
    st.subheader(f"Summary for {selected_month}")

    # Stack metrics vertically to preserve space for large values
    st.markdown("<div style='font-size: 14px'>", unsafe_allow_html=True)
    st.metric("Short-Term Gain/Loss", f"${total_st:,.2f}")
    st.metric("Long-Term Gain/Loss", f"${total_lt:,.2f}")

    if include_impairment_expense:
        total_impairment = combined['impairmentExpense'].sum()
        st.metric("Impairment Expense", f"${total_impairment:,.2f}")

    if include_impairment_reversal:
        total_reversal = combined['impairmentReversal'].sum()
        st.metric("Impairment Reversal", f"${total_reversal:,.2f}")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("📁 Per Asset & Inventory Details")
    with st.expander("Click to view detailed table"):
        st.dataframe(combined)


if __name__ == "__main__":
    main()
