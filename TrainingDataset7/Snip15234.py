def test_exclude_duplicate_values(self):
        class ExcludedFields2(admin.ModelAdmin):
            exclude = ("name", "name")

        errors = ExcludedFields2(Book, AdminSite()).check()
        expected = [
            checks.Error(
                "The value of 'exclude' contains duplicate field(s).",
                hint="Remove duplicates of 'name'.",
                obj=ExcludedFields2,
                id="admin.E015",
            )
        ]
        self.assertEqual(errors, expected)