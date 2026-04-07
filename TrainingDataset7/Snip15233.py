def test_exclude_values(self):
        """
        Tests for basic system checks of 'exclude' option values (#12689)
        """

        class ExcludedFields1(admin.ModelAdmin):
            exclude = "foo"

        errors = ExcludedFields1(Book, AdminSite()).check()
        expected = [
            checks.Error(
                "The value of 'exclude' must be a list or tuple.",
                obj=ExcludedFields1,
                id="admin.E014",
            )
        ]
        self.assertEqual(errors, expected)