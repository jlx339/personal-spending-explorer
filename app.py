"""Run with: uv run streamlit run app.py."""
from pathlib import Path

import streamlit as st

from components.dashboard import render_dashboard
from utils.session import apply_upload, reset_filters
from utils.spending_math import filter_transactions

ROOT = Path(__file__).resolve().parent
DEMO_PATH = ROOT / 'sample_data' / 'sample_spending.csv'


def use_demo_data() -> None:
    apply_upload(st.session_state, DEMO_PATH.read_bytes(), 'Fictional demo data')
    # Changing the uploader key clears a previous file without attempting to
    # mutate Streamlit's read-only file-uploader value.
    st.session_state['upload_revision'] = st.session_state.get('upload_revision', 0) + 1


def handle_upload(widget_key: str) -> None:
    uploaded = st.session_state.get(widget_key)
    if uploaded is not None:
        apply_upload(st.session_state, uploaded.getvalue(), uploaded.name)


def main() -> None:
    st.set_page_config(page_title='Personal Spending Explorer', page_icon='🍁', layout='wide')
    if 'transactions' not in st.session_state:
        use_demo_data()

    st.markdown('''
    <style>
    .block-container {max-width: 1280px; padding-top: 2.5rem; padding-bottom: 3rem;}
    h1 {letter-spacing: -0.035em;}
    [data-testid="stMetric"] {background: #fff; border: 1px solid #e1e8e2;
        border-radius: 14px; padding: 18px; min-height: 122px;}
    [data-testid="stMetricValue"] {font-variant-numeric: tabular-nums;}
    [data-testid="stSidebar"] {border-right: 1px solid #e1e8e2;}
    </style>
    ''', unsafe_allow_html=True)
    st.title('Personal Spending Explorer')
    st.caption(f"{st.session_state['source']} · CAD · Expenses only")
    st.write('A clearer picture of where your money goes.')

    transactions = st.session_state['transactions']
    start, end = min(item.date for item in transactions), max(item.date for item in transactions)
    categories = sorted({item.category for item in transactions})
    methods = sorted({item.payment_method for item in transactions})

    revision = st.session_state['filter_revision']
    with st.sidebar:
        st.subheader('Your data')
        upload_key = f"upload_{st.session_state.get('upload_revision', 0)}"
        st.file_uploader('Upload a spending CSV', type=['csv'], key=upload_key,
                         help='UTF-8 CSV, up to 5 MB. All amounts must be positive CAD expenses.',
                         on_change=handle_upload, args=(upload_key,))
        st.button('Use demo data', key='use_demo', on_click=use_demo_data, width='stretch')
        st.caption('Explore 192 fictional transactions. No account or API key needed.')
        with st.expander('CSV format'):
            st.code('date,merchant,category,amount,payment_method\n2026-04-02,Corner Market,Groceries,64.25,Debit', language='csv')
            st.write('Required: ISO dates, merchant, category, positive CAD amount, and payment method. Extra columns are ignored. Income and refunds are not supported.')
            st.download_button('Download sample CSV', data=DEMO_PATH.read_bytes(),
                               file_name='sample_spending_cad.csv', mime='text/csv', key='download_sample')
        st.divider()
        st.subheader('Filters')
        st.button('Reset filters', key='reset_filters', on_click=reset_filters,
                  args=(st.session_state,), width='stretch')
        dates = st.date_input('Date range', value=(start, end), min_value=start,
                              max_value=end, format='YYYY-MM-DD', key=f'date_range_{revision}')
        selected_categories = st.multiselect('Categories', categories, default=categories, key=f'category_filter_{revision}')
        selected_methods = st.multiselect('Payment methods', methods, default=methods, key=f'payment_filter_{revision}')
        st.caption('Clearing a selection shows no expenses. Reset restores all records.')
        st.divider()
        st.caption('Your uploads stay in this app session and are not saved to disk. Refreshing starts a new demo session.')

    if st.session_state.get('upload_error'):
        st.error('Could not import the CSV. Your previous dataset is still active.\n\n' + st.session_state['upload_error'])
    for notice in st.session_state.get('notices', ()):
        st.info(notice)
    if not isinstance(dates, (tuple, list)) or len(dates) != 2:
        st.info('Select both a start date and an end date to explore your spending.')
        return
    selected_start, selected_end = dates
    if selected_start > selected_end:
        st.error('The start date must be on or before the end date.')
        return
    filtered = filter_transactions(transactions, selected_start, selected_end, selected_categories, selected_methods)
    render_dashboard(filtered, selected_start, selected_end, revision)


if __name__ == '__main__':
    main()
