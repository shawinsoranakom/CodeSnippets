def test_errors_aggregated(self):
        errors = check_templates(None)
        self.assertEqual(errors, [Error("Example")] * 2)