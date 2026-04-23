def test_values_expression_containing_percent_sign_deprecation_warns_once(self):
        msg = "Using percent signs in a column alias is deprecated."
        with self.assertWarnsMessage(RemovedInDjango70Warning, msg) as cm:
            Company.objects.values(**{"alias%": F("id")})
        self.assertEqual(len(cm.warnings), 1)