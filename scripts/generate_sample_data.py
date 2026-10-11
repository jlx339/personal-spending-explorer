"""Generate fictional CAD transactions without downloads or personal data."""
from __future__ import annotations

import calendar
import random
from datetime import date
from pathlib import Path

from utils.data_processing import Transaction, export_csv


def generate_transactions(seed: int = 42) -> tuple[Transaction, ...]:
    rng = random.Random(seed)
    transactions = []
    patterns = [
        ('Groceries', ['Maple Market', 'Northside Grocer', 'Corner Pantry'], 8, 2800, 12500),
        ('Dining', ['Harbour Cafe', 'Noodle Corner', 'Oak Street Kitchen'], 8, 650, 6500),
        ('Transport', ['City Transit', 'Downtown Parking', 'Neighbourhood Taxi'], 5, 350, 4500),
        ('Shopping', ['Everyday Goods', 'Paper & Pine', 'Trail Outfitters'], 4, 1500, 14000),
        ('Entertainment', ['Local Cinema', 'Music Subscription', 'Community Events'], 4, 999, 5500),
    ]
    for month in range(4, 10):
        transactions.append(Transaction(date(2026, month, 1), 'Maple Apartments', 'Rent', 185000, 'Debit'))
        transactions.append(Transaction(date(2026, month, 5), 'Home Internet', 'Utilities', 7500, 'Credit'))
        transactions.append(Transaction(date(2026, month, 15), 'City Hydro', 'Utilities', rng.randint(5500, 9500), 'Debit'))
        for category, merchants, count, low, high in patterns:
            for index in range(count):
                day = rng.randint(1, calendar.monthrange(2026, month)[1])
                if category == 'Groceries' and index == 0:
                    day = calendar.monthrange(2026, month)[1]
                amount = rng.randint(low, high)
                if month == 8 and category == 'Shopping':
                    amount += 6500  # An intentional seasonal spike for exploration.
                transactions.append(Transaction(
                    date(2026, month, day), rng.choice(merchants), category,
                    amount, rng.choice(['Credit', 'Debit', 'Cash']),
                ))
    return tuple(sorted(transactions, key=lambda item: (item.date, item.merchant, item.amount_cents)))


if __name__ == '__main__':
    destination = Path(__file__).resolve().parents[1] / 'sample_data' / 'sample_spending.csv'
    destination.parent.mkdir(parents=True, exist_ok=True)
    records = generate_transactions()
    destination.write_bytes(export_csv(records))
    print(f'Wrote {len(records)} fictional CAD transactions to {destination}')
