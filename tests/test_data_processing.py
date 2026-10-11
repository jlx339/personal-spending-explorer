import unittest

from utils.data_processing import ValidationError, export_csv, load_csv

HEADER = 'date,merchant,category,amount,payment_method\n'
VALID = '2026-04-02,Corner Market,Groceries,64.25,Debit\n'


class DataProcessingTests(unittest.TestCase):
    def test_loads_exact_integer_cents(self):
        result = load_csv((HEADER + VALID).encode())
        self.assertEqual(result.transactions[0].amount_cents, 6425)
        self.assertEqual(result.transactions[0].date.isoformat(), '2026-04-02')

    def test_accepts_bom_and_trims_header_and_text(self):
        data = '\ufeff date ,merchant,category,amount,payment_method\n2026-04-02, Market , Groceries ,0.10, Debit \n'
        transaction = load_csv(data.encode()).transactions[0]
        self.assertEqual((transaction.merchant, transaction.category, transaction.payment_method), ('Market', 'Groceries', 'Debit'))
        self.assertEqual(transaction.amount_cents, 10)

    def test_extra_columns_generate_notice(self):
        result = load_csv((HEADER.strip() + ',note\n' + VALID.strip() + ',hello\n').encode())
        self.assertEqual(len(result.transactions), 1)
        self.assertIn('note', result.notices[0])

    def test_preserves_legitimate_duplicate_transactions(self):
        self.assertEqual(len(load_csv((HEADER + VALID * 2).encode()).transactions), 2)

    def test_rejects_invalid_amounts_with_row_number(self):
        for amount in ['0', '-1', '1.001', 'NaN', 'Infinity', '1e2', '$12.00', '']:
            with self.subTest(amount=amount), self.assertRaises(ValidationError) as caught:
                load_csv((HEADER + f'2026-04-02,Shop,Shopping,{amount},Credit\n').encode())
            self.assertIn('2', str(caught.exception))

    def test_rejects_invalid_or_non_iso_dates(self):
        for day in ['2026-02-30', '04/02/2026', '20260402', '2026-4-2']:
            with self.subTest(day=day), self.assertRaises(ValidationError):
                load_csv((HEADER + f'{day},Shop,Shopping,10.00,Credit\n').encode())

    def test_rejects_missing_columns(self):
        with self.assertRaisesRegex(ValidationError, 'amount'):
            load_csv(b'date,merchant,category,payment_method\n2026-04-02,Shop,Shopping,Credit\n')

    def test_rejects_missing_text_and_uneven_rows(self):
        for row in ['2026-04-02,,Shopping,10,Credit\n', '2026-04-02,Shop,Shopping,10\n', VALID.strip() + ',unexpected\n']:
            with self.subTest(row=row), self.assertRaises(ValidationError):
                load_csv((HEADER + row).encode())

    def test_rejects_duplicate_headers(self):
        with self.assertRaises(ValidationError):
            load_csv((HEADER.strip() + ',amount\n' + VALID.strip() + ',20\n').encode())

    def test_rejects_non_utf8_empty_and_header_only_files(self):
        for data in [b'\xff', b'', HEADER.encode()]:
            with self.subTest(data=data), self.assertRaises(ValidationError):
                load_csv(data)

    def test_rejects_oversized_file(self):
        with self.assertRaisesRegex(ValidationError, '5 MB'):
            load_csv(b'a' * (5 * 1024 * 1024 + 1))

    def test_rejects_malformed_quoted_csv(self):
        with self.assertRaises(ValidationError):
            load_csv((HEADER + '2026-04-02,"unterminated,Shopping,10,Credit\n').encode())

    def test_export_round_trip_preserves_cents_and_quoted_merchants(self):
        transactions = load_csv((HEADER + '2026-04-02,"Cafe, North",Dining,0.10,Cash\n' + VALID).encode()).transactions
        exported = export_csv(transactions)
        self.assertIn(b'0.10', exported)
        self.assertEqual(load_csv(exported).transactions, transactions)

    def test_empty_export_retains_original_schema(self):
        self.assertEqual(export_csv([]).decode().strip(), HEADER.strip())


if __name__ == '__main__':
    unittest.main()
