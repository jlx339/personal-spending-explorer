import unittest

from utils.data_processing import load_csv
from utils.session import apply_upload, reset_filters

VALID = b'date,merchant,category,amount,payment_method\n2026-04-02,Shop,Shopping,10.00,Credit\n'


class SessionTests(unittest.TestCase):
    def test_invalid_upload_retains_previous_valid_dataset_and_filters(self):
        previous = load_csv(VALID).transactions
        state = {'transactions': previous, 'source': 'Fictional demo data', 'category_filter': ['Shopping']}
        self.assertFalse(apply_upload(state, b'invalid', 'bad.csv'))
        self.assertEqual(state['transactions'], previous)
        self.assertEqual(state['source'], 'Fictional demo data')
        self.assertEqual(state['category_filter'], ['Shopping'])
        self.assertTrue(state['upload_error'])

    def test_valid_upload_replaces_data_and_clears_stale_controls(self):
        state = {'transactions': (), 'category_filter': ['Rent'], 'payment_filter': ['Cash'], 'date_range': (), 'merchant_search': 'Old'}
        self.assertTrue(apply_upload(state, VALID, 'expenses.csv'))
        self.assertEqual(len(state['transactions']), 1)
        self.assertEqual(state['source'], 'expenses.csv')
        self.assertEqual(state['upload_error'], '')
        for key in ['category_filter', 'payment_filter', 'date_range', 'merchant_search']:
            self.assertNotIn(key, state)

    def test_repeated_valid_upload_clears_previous_error(self):
        state = {}
        apply_upload(state, b'bad', 'bad.csv')
        apply_upload(state, VALID, 'good.csv')
        self.assertEqual(state['upload_error'], '')

    def test_reset_changes_widget_identity_to_prevent_frontend_restore(self):
        state = {'filter_revision': 3, 'merchant_search': 'old'}
        reset_filters(state)
        self.assertEqual(state['filter_revision'], 4)
        self.assertNotIn('merchant_search', state)

    def test_reset_filters_preserves_dataset(self):
        state = {'transactions': (1,), 'source': 'demo', 'merchant_search': 'text', 'date_range': (1, 2)}
        reset_filters(state)
        self.assertEqual(state, {'transactions': (1,), 'source': 'demo', 'filter_revision': 1})


if __name__ == '__main__':
    unittest.main()
