import unittest
from datetime import date
from decimal import Decimal

from utils.data_processing import Transaction
from utils.spending_math import filter_transactions, format_cad, group_totals, monthly_totals, search_transactions, summarize

START = date(2026, 4, 1)
END = date(2026, 6, 30)
RECORDS = (
    Transaction(START, 'Market', 'Groceries', 1000, 'Debit'),
    Transaction(date(2026, 4, 30), 'Cafe [North]', 'Dining', 2010, 'Credit'),
    Transaction(END, 'Market', 'Groceries', 500, 'Cash'),
)


class SpendingMathTests(unittest.TestCase):
    def test_totals_and_monthly_average_include_empty_month(self):
        summary = summarize(RECORDS, START, END)
        self.assertEqual(summary.total_cents, 3510)
        self.assertEqual(summary.average_monthly_cents, Decimal(1170))
        self.assertEqual(summary.transaction_count, 3)
        self.assertEqual(summary.largest_expense_cents, 2010)
        self.assertEqual(summary.month_count, 3)

    def test_combined_filters_use_inclusive_dates(self):
        rows = filter_transactions(RECORDS, START, END, ['Groceries'], ['Debit', 'Cash'])
        self.assertEqual(rows, (RECORDS[0], RECORDS[2]))
        self.assertEqual(filter_transactions(RECORDS, START, START, ['Groceries'], ['Debit']), (RECORDS[0],))

    def test_empty_selection_means_no_transactions(self):
        self.assertEqual(filter_transactions(RECORDS, START, END, [], ['Debit']), ())
        self.assertEqual(filter_transactions(RECORDS, START, END, ['Groceries'], []), ())

    def test_empty_summary_has_zero_totals_and_no_largest_expense(self):
        summary = summarize((), START, END)
        self.assertEqual(summary.total_cents, 0)
        self.assertEqual(summary.average_monthly_cents, 0)
        self.assertEqual(summary.transaction_count, 0)
        self.assertIsNone(summary.largest_expense_cents)

    def test_monthly_series_is_chronological_and_fills_gaps(self):
        self.assertEqual(monthly_totals(RECORDS, START, END), [('2026-04', 3010), ('2026-05', 0), ('2026-06', 500)])

    def test_partial_months_and_year_boundary_count_calendar_months(self):
        self.assertEqual(summarize((), date(2025, 12, 31), date(2026, 1, 1)).month_count, 2)
        self.assertEqual(monthly_totals((), date(2025, 12, 31), date(2026, 1, 1)), [('2025-12', 0), ('2026-01', 0)])

    def test_invalid_date_range_is_rejected(self):
        with self.assertRaises(ValueError):
            summarize(RECORDS, END, START)

    def test_groups_are_ranked_by_spending(self):
        self.assertEqual(group_totals(RECORDS, 'category'), [('Dining', 2010), ('Groceries', 1500)])
        self.assertEqual(group_totals(RECORDS, 'merchant'), [('Cafe [North]', 2010), ('Market', 1500)])

    def test_search_is_case_insensitive_literal_and_table_only(self):
        self.assertEqual(search_transactions(RECORDS, ' [north] '), (RECORDS[1],))
        self.assertEqual(search_transactions(RECORDS, ''), RECORDS)
        self.assertEqual(search_transactions(RECORDS, 'missing'), ())
        self.assertEqual(summarize(RECORDS, START, END).total_cents, 3510)

    def test_currency_format_is_cad_with_exact_half_up_rounding(self):
        self.assertEqual(format_cad(123456), 'CA$1,234.56')
        self.assertEqual(format_cad(Decimal('100.5')), 'CA$1.01')
        self.assertEqual(format_cad(None), '—')


if __name__ == '__main__':
    unittest.main()
