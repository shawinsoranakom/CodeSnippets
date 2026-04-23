def test_failure_view_valid_class_based(self):
        self.assertEqual(csrf.check_csrf_failure_view(None), [])