def test_alias_containing_percent_sign_deprecation(self):
        msg = "Using percent signs in a column alias is deprecated."
        with self.assertRaisesMessage(RemovedInDjango70Warning, msg):
            Book.objects.annotate(**{"alias%": Value(1)})