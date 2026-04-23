def test_graceful_m2m_fail(self):
        """
        Regression test for #12203/#12237 - Fail more gracefully when a M2M
        field that specifies the 'through' option is included in the 'fields'
        or the 'fieldsets' ModelAdmin options.
        """

        class BookAdmin(admin.ModelAdmin):
            fields = ["authors"]

        errors = BookAdmin(Book, AdminSite()).check()
        expected = [
            checks.Error(
                "The value of 'fields' cannot include the ManyToManyField 'authors', "
                "because that field manually specifies a relationship model.",
                obj=BookAdmin,
                id="admin.E013",
            )
        ]
        self.assertEqual(errors, expected)