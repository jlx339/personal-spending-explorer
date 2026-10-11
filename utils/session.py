"""Atomic dataset replacement, shared by UI callbacks and behavior tests."""
from __future__ import annotations

from typing import MutableMapping

from utils.data_processing import ValidationError, load_csv

FILTER_KEYS = ('date_range', 'category_filter', 'payment_filter', 'merchant_search')


def reset_filters(state: MutableMapping) -> None:
    # Fresh keys force Streamlit to discard the browser's previous widget values.
    state['filter_revision'] = state.get('filter_revision', 0) + 1
    for key in FILTER_KEYS:
        state.pop(key, None)


def apply_upload(state: MutableMapping, content: bytes, source: str) -> bool:
    try:
        result = load_csv(content)
    except ValidationError as exc:
        state['upload_error'] = str(exc)
        return False
    state['transactions'] = result.transactions
    state['source'] = source
    state['notices'] = result.notices
    state['upload_error'] = ''
    reset_filters(state)
    return True
