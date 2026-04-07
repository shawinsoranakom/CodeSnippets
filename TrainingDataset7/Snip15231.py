def test_fieldsets_fields_non_tuple(self):
        """
        The first fieldset's fields must be a list/tuple.
        """

        class NotATupleAdmin(admin.ModelAdmin):
            list_display = ["pk", "title"]
            list_editable = ["title"]
            fieldsets = [
                (None, {"fields": "title"}),  # not a tuple
            ]

        errors = NotATupleAdmin(Song, AdminSite()).check()
        expected = [
            checks.Error(
                "The value of 'fieldsets[0][1]['fields']' must be a list or tuple.",
                obj=NotATupleAdmin,
                id="admin.E008",
            )
        ]
        self.assertEqual(errors, expected)