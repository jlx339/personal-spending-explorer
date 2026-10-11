import unittest
from collections import Counter
from pathlib import Path

from scripts.generate_sample_data import generate_transactions
from utils.data_processing import export_csv, load_csv


class SampleDataTests(unittest.TestCase):
    def test_seed_reproduces_data_and_can_vary_it(self):
        self.assertEqual(generate_transactions(42), generate_transactions(42))
        self.assertNotEqual(generate_transactions(42), generate_transactions(43))

    def test_contains_six_months_recurring_rent_and_varied_expenses(self):
        records = generate_transactions()
        self.assertTrue(180 <= len(records) <= 220)
        self.assertEqual(sorted({r.date.month for r in records}), [4, 5, 6, 7, 8, 9])
        rent = [r for r in records if r.category == 'Rent']
        self.assertEqual(len(rent), 6)
        self.assertTrue(all(r.amount_cents == 185000 for r in rent))
        self.assertEqual({r.payment_method for r in records}, {'Credit', 'Debit', 'Cash'})
        self.assertEqual(len({r.category for r in records}), 7)
        self.assertTrue(all(r.amount_cents > 0 for r in records))

    def test_generated_csv_is_valid_and_matches_bundled_file(self):
        records = generate_transactions()
        encoded = export_csv(records)
        self.assertEqual(load_csv(encoded).transactions, records)
        self.assertEqual(Path('sample_data/sample_spending.csv').read_bytes(), encoded)


if __name__ == '__main__':
    unittest.main()
