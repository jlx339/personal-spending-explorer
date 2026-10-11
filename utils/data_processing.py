"""CSV boundary: validate expenses once and keep all money in integer cents."""
from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass
from datetime import date
from typing import Iterable

COLUMNS = ('date', 'merchant', 'category', 'amount', 'payment_method')
MAX_FILE_BYTES = 5 * 1024 * 1024


@dataclass(frozen=True)
class Transaction:
    date: date
    merchant: str
    category: str
    amount_cents: int
    payment_method: str


@dataclass(frozen=True)
class LoadResult:
    transactions: tuple[Transaction, ...]
    notices: tuple[str, ...] = ()


class ValidationError(ValueError):
    """A user-readable file or row validation failure."""


def _amount_cents(value: str) -> int:
    # Limit digit length to keep uploaded values usable in chart/table libraries.
    if not re.fullmatch(r'[0-9]{1,15}(?:\.[0-9]{1,2})?', value):
        raise ValueError('amount must be a positive CAD number with at most two decimal places (up to 15 whole digits)')
    whole, _, fraction = value.partition('.')
    cents = int(whole) * 100 + int(fraction.ljust(2, '0') or '0')
    if cents <= 0:
        raise ValueError('amount must be greater than zero')
    return cents


def load_csv(content: bytes) -> LoadResult:
    if len(content) > MAX_FILE_BYTES:
        raise ValidationError('Choose a CSV file no larger than 5 MB.')
    try:
        text = content.decode('utf-8-sig')
    except UnicodeDecodeError as exc:
        raise ValidationError('Save your CSV with UTF-8 encoding and try again.') from exc
    reader = csv.DictReader(io.StringIO(text, newline=''), strict=True)
    try:
        headers = reader.fieldnames
        if not headers:
            raise ValidationError('The CSV is empty. Include a header and at least one transaction.')
        headers = [header.strip() for header in headers]
        if len(headers) != len(set(headers)):
            raise ValidationError('The CSV contains duplicate column names.')
        missing = [name for name in COLUMNS if name not in headers]
        if missing:
            raise ValidationError('Missing required columns: ' + ', '.join(missing))
        reader.fieldnames = headers
        extras = [name for name in headers if name not in COLUMNS]
        notices = ('Ignored extra columns: ' + ', '.join(extras),) if extras else ()
        transactions = []
        errors = []
        for row in reader:
            try:
                if None in row or any(value is None for value in row.values()):
                    raise ValueError('the number of fields does not match the header')
                values = {name: row[name].strip() for name in COLUMNS}
                if any(not value for value in values.values()):
                    raise ValueError('all five required fields must have values')
                if not re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}', values['date']):
                    raise ValueError('date must use YYYY-MM-DD')
                try:
                    day = date.fromisoformat(values['date'])
                except ValueError as exc:
                    raise ValueError('date must be a real calendar date in YYYY-MM-DD format') from exc
                transactions.append(Transaction(
                    day, values['merchant'], values['category'],
                    _amount_cents(values['amount']), values['payment_method'],
                ))
            except ValueError as exc:
                errors.append(f'CSV row {reader.line_num}: {exc}.')
                if len(errors) == 20:
                    break
        if errors:
            message = '\n'.join(errors)
            if len(errors) == 20:
                message += '\nShowing the first 20 errors. No transactions were imported.'
            raise ValidationError(message)
        if not transactions:
            raise ValidationError('The CSV has no transactions. Add at least one expense row.')
        return LoadResult(tuple(transactions), notices)
    except csv.Error as exc:
        raise ValidationError(f'CSV row {reader.line_num}: malformed CSV. Check quotes and field lengths.') from exc


def export_csv(transactions: Iterable[Transaction]) -> bytes:
    output = io.StringIO(newline='')
    writer = csv.writer(output, lineterminator='\n')
    writer.writerow(COLUMNS)
    for item in transactions:
        writer.writerow((item.date.isoformat(), item.merchant, item.category,
                         f'{item.amount_cents // 100}.{item.amount_cents % 100:02d}',
                         item.payment_method))
    return output.getvalue().encode('utf-8')
