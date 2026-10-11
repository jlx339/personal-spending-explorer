"""UI behavior checks; skipped explicitly when Streamlit isn't installed."""
import importlib.util
import unittest
from datetime import date
from pathlib import Path

from utils.session import apply_upload

HAS_STREAMLIT = importlib.util.find_spec('streamlit') is not None
if HAS_STREAMLIT:
    from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[1] / 'app.py')


@unittest.skipUnless(HAS_STREAMLIT, 'Streamlit is not installed; run uv sync, then uv run pytest.')
class DashboardTests(unittest.TestCase):
    def setUp(self):
        self.app = AppTest.from_file(APP, default_timeout=15).run()

    def widget_key(self, name):
        return f"{name}_{self.app.session_state['filter_revision']}"

    def test_demo_starts_with_metrics_and_no_exception(self):
        self.assertFalse(self.app.exception)
        self.assertEqual(self.app.metric[2].value, '192')
        self.assertIn('Fictional demo data', self.app.caption[0].value)
        self.assertEqual(self.app.metric[0].value, 'CA$20,958.14')
        self.assertEqual(self.app.metric[1].value, 'CA$3,493.02')

    def test_clearing_category_filter_produces_empty_state(self):
        self.app.multiselect(key=self.widget_key('category_filter')).set_value([]).run()
        self.assertFalse(self.app.exception)
        self.assertEqual(self.app.metric[0].value, 'CA$0.00')
        self.assertEqual(self.app.metric[2].value, '0')
        self.assertTrue(self.app.info)

    def test_merchant_search_changes_table_but_not_overview(self):
        previous = self.app.metric[0].value
        self.app.text_input(key=self.widget_key('merchant_search')).set_value('no-such-merchant').run()
        self.assertFalse(self.app.exception)
        self.assertEqual(self.app.metric[0].value, previous)
        self.assertEqual(len(self.app.dataframe[0].value), 0)

    def test_reset_restores_all_categories_and_clears_search(self):
        self.app.multiselect(key=self.widget_key('category_filter')).set_value(['Rent']).run()
        self.app.text_input(key=self.widget_key('merchant_search')).set_value('Maple').run()
        self.app.button(key='reset_filters').click().run()
        self.assertFalse(self.app.exception)
        self.assertEqual(self.app.metric[2].value, '192')
        self.assertEqual(self.app.text_input(key=self.widget_key('merchant_search')).value, '')

    def test_partial_date_range_shows_guidance(self):
        self.app.date_input(key=self.widget_key('date_range')).set_value((date(2026, 4, 1),)).run()
        self.assertFalse(self.app.exception)
        self.assertTrue(self.app.info)
        self.assertEqual(len(self.app.metric), 0)

    def test_replacement_clears_stale_filters_and_recalculates_metrics(self):
        # File uploads are not exposed by AppTest. Apply the exact upload
        # transition, then rerun the SAME session so frontend widgets survive.
        self.app.multiselect(key=self.widget_key('category_filter')).set_value(['Rent']).run()
        self.app.text_input(key=self.widget_key('merchant_search')).set_value('Maple').run()
        state = {
            key: self.app.session_state[key]
            for key in ('transactions', 'source', 'notices', 'upload_error',
                        'upload_revision', 'filter_revision')
        }
        csv = b'date,merchant,category,amount,payment_method\n2026-09-01,Bookstore,Books,12.50,Cash\n'
        self.assertTrue(apply_upload(state, csv, 'books.csv'))
        for key, value in state.items():
            self.app.session_state[key] = value
        self.app.run()
        self.assertFalse(self.app.exception)
        self.assertEqual(self.app.metric[0].value, 'CA$12.50')
        self.assertEqual(self.app.multiselect(key=self.widget_key('category_filter')).value, ['Books'])
        self.assertEqual(self.app.multiselect(key=self.widget_key('payment_filter')).value, ['Cash'])
        self.assertEqual(self.app.text_input(key=self.widget_key('merchant_search')).value, '')



if __name__ == '__main__':
    unittest.main()
