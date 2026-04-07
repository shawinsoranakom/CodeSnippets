def test_pk_not_editable(self):
        # PKs cannot be edited in the list.
        class SongAdmin(admin.ModelAdmin):
            list_display = ["title", "id"]
            list_editable = ["id"]

        errors = SongAdmin(Song, AdminSite()).check()
        expected = [
            checks.Error(
                "The value of 'list_editable[0]' refers to 'id', which is not editable "
                "through the admin.",
                obj=SongAdmin,
                id="admin.E125",
            )
        ]
        self.assertEqual(errors, expected)