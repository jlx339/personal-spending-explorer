"""Exact spending calculations; presentation libraries never compute totals."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable, Optional

from utils.data_processing import Transaction


@dataclass(frozen=True)
class SpendingSummary:
    total_cents: int
    average_monthly_cents: Decimal
    transaction_count: int
    largest_expense_cents: Optional[int]
    month_count: int


def _month_count(start: date, end: date) -> int:
    if start > end:
        raise ValueError('Start date must be on or before end date.')
    return (end.year - start.year) * 12 + end.month - start.month + 1


def filter_transactions(
    transactions: Iterable[Transaction], start: date, end: date,
    categories: Iterable[str], payment_methods: Iterable[str],
) -> tuple[Transaction, ...]:
    _month_count(start, end)
    categories, payment_methods = set(categories), set(payment_methods)
    return tuple(item for item in transactions
                 if start <= item.date <= end
                 and item.category in categories
                 and item.payment_method in payment_methods)


def summarize(transactions: Iterable[Transaction], start: date, end: date) -> SpendingSummary:
    """Summarize already-filtered expenses over the selected calendar months."""
    records = tuple(transactions)
    months = _month_count(start, end)
    total = sum(item.amount_cents for item in records)
    largest = max((item.amount_cents for item in records), default=None)
    return SpendingSummary(total, Decimal(total) / months, len(records), largest, months)


def monthly_totals(transactions: Iterable[Transaction], start: date, end: date) -> list[tuple[str, int]]:
    """Return a gap-filled chronological series for already-filtered records."""
    months = _month_count(start, end)
    first = start.year * 12 + start.month - 1
    totals = {f'{index // 12:04d}-{index % 12 + 1:02d}': 0 for index in range(first, first + months)}
    for item in transactions:
        month = item.date.strftime('%Y-%m')
        if start <= item.date <= end:
            totals[month] += item.amount_cents
    return list(totals.items())


def group_totals(transactions: Iterable[Transaction], field: str) -> list[tuple[str, int]]:
    if field not in {'category', 'merchant', 'payment_method'}:
        raise ValueError('Group by category, merchant, or payment_method.')
    totals = Counter()
    for item in transactions:
        totals[getattr(item, field)] += item.amount_cents
    return sorted(totals.items(), key=lambda item: (-item[1], item[0].casefold(), item[0]))


def search_transactions(transactions: Iterable[Transaction], query: str) -> tuple[Transaction, ...]:
    query = query.strip().casefold()
    return tuple(item for item in transactions if query in item.merchant.casefold())


def format_cad(cents: Optional[int | Decimal]) -> str:
    if cents is None:
        return '—'
    dollars = (Decimal(cents) / 100).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    return f'CA${dollars:,.2f}'
