def test_failure_view_valid_deferred_annotations(self):
        self.assertEqual(csrf.check_csrf_failure_view(None), [])