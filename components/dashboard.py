"""CAD metric cards, interactive charts, and searchable expense exports."""
from __future__ import annotations

from datetime import date
from typing import Iterable

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.data_processing import Transaction, export_csv
from utils.spending_math import format_cad, group_totals, monthly_totals, search_transactions, summarize

TEAL = '#147D64'
BLUE = '#3C6E9C'
ORANGE = '#BE692F'


def _chart_style(figure: go.Figure) -> go.Figure:
    figure.update_layout(
        height=330, margin=dict(l=12, r=12, t=15, b=15),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Arial, sans-serif', color='#182F35', size=12),
        showlegend=False, hoverlabel=dict(bgcolor='white'),
    )
    figure.update_xaxes(showgrid=False, zeroline=False)
    figure.update_yaxes(gridcolor='#E3E8E3', zeroline=False)
    return figure


def _ranked_chart(totals: list[tuple[str, int]], color: str) -> go.Figure:
    rows = list(reversed(totals))
    figure = go.Figure(go.Bar(
        x=[cents / 100 for _, cents in rows], y=[label for label, _ in rows],
        orientation='h', marker_color=color,
        customdata=[format_cad(cents) for _, cents in rows],
        hovertemplate='%{y}<br>%{customdata}<extra></extra>',
    ))
    _chart_style(figure)
    figure.update_xaxes(title='Spending (CAD)', tickprefix='CA$')
    figure.update_yaxes(type='category', categoryorder='array', categoryarray=[label for label, _ in rows])
    # Keep every category readable when a user uploads a large taxonomy.
    figure.update_layout(height=max(330, min(1200, len(rows) * 28 + 60)))
    return figure


def render_dashboard(transactions: Iterable[Transaction], start: date, end: date, revision: int) -> None:
    records = tuple(transactions)
    summary = summarize(records, start, end)
    st.subheader('Spending overview')
    st.caption(f'{start:%d %b %Y} – {end:%d %b %Y} · {summary.month_count} calendar months')
    cards = st.columns(4)
    cards[0].metric('Total spending', format_cad(summary.total_cents))
    cards[1].metric('Average per month', format_cad(summary.average_monthly_cents),
                    help='Total filtered spending divided by all calendar months touched by the selected date range, including months with no expenses.')
    cards[2].metric('Transactions', f'{summary.transaction_count:,}')
    cards[3].metric('Largest expense', format_cad(summary.largest_expense_cents))

    if not records:
        st.info('No expenses match these filters. Choose more categories or payment methods, or reset the filters.')
    else:
        st.write('')
        trend_column, category_column = st.columns([1.25, 1])
        with trend_column:
            with st.container(border=True):
                st.subheader('Monthly spending')
                series = monthly_totals(records, start, end)
                figure = go.Figure(go.Scatter(
                    x=[month for month, _ in series], y=[cents / 100 for _, cents in series],
                    mode='lines+markers', fill='tozeroy',
                    line=dict(color=TEAL, width=3), marker=dict(size=8),
                    fillcolor='rgba(20,125,100,0.10)',
                    customdata=[format_cad(cents) for _, cents in series],
                    hovertemplate='%{x}<br>%{customdata}<extra></extra>',
                ))
                _chart_style(figure)
                figure.update_xaxes(type='category')
                figure.update_yaxes(title='Spending (CAD)', tickprefix='CA$', rangemode='tozero')
                st.plotly_chart(figure, key='monthly_chart',
                                config={'displayModeBar': False})
        with category_column:
            with st.container(border=True):
                st.subheader('Where it goes')
                st.plotly_chart(_ranked_chart(group_totals(records, 'category'), BLUE),
                                key='category_chart', config={'displayModeBar': False})
        with st.container(border=True):
            st.subheader('Top merchants')
            st.caption('The ten merchants with the highest spending in your current selection.')
            st.plotly_chart(_ranked_chart(group_totals(records, 'merchant')[:10], ORANGE),
                            key='merchant_chart', config={'displayModeBar': False})

    st.divider()
    st.subheader('Transactions')
    st.caption('Search affects this table and its download only. Overview metrics and charts use the sidebar filters.')
    query = st.text_input('Search merchants', placeholder='Try “Maple” or “Cafe”', key=f'merchant_search_{revision}')
    displayed = tuple(sorted(search_transactions(records, query), key=lambda item: item.date, reverse=True))
    table = pd.DataFrame([
        {'Date': item.date, 'Merchant': item.merchant, 'Category': item.category,
         'Amount (CAD)': format_cad(item.amount_cents), 'Payment method': item.payment_method}
        for item in displayed
    ], columns=['Date', 'Merchant', 'Category', 'Amount (CAD)', 'Payment method'])
    st.caption(f'{len(displayed):,} displayed transactions · {format_cad(sum(item.amount_cents for item in displayed))}')
    st.dataframe(table, hide_index=True, use_container_width=True,
                 column_config={'Date': st.column_config.DateColumn(format='YYYY-MM-DD')})
    if records and not displayed:
        st.info('No merchants match your search. Clear the search to see all filtered transactions.')
    st.download_button('Download displayed transactions', data=export_csv(displayed),
                       file_name='spending_cad_filtered.csv', mime='text/csv',
                       key='download_filtered', disabled=not displayed)
