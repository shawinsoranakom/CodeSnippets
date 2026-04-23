def test_nonfirst_fieldset(self):
        """
        The second fieldset's fields must be a list/tuple.
        """

        class NotATupleAdmin(admin.ModelAdmin):
            fieldsets = [
                (None, {"fields": ("title",)}),
                ("foo", {"fields": "author"}),  # not a tuple
            ]

        errors = NotATupleAdmin(Song, AdminSite()).check()
        expected = [
            checks.Error(
                "The value of 'fieldsets[1][1]['fields']' must be a list or tuple.",
                obj=NotATupleAdmin,
                id="admin.E008",
            )
        ]
        self.assertEqual(errors, expected)