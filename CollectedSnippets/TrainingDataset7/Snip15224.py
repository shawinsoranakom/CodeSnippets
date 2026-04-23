def test_list_editable_not_a_list_or_tuple(self):
        class SongAdmin(admin.ModelAdmin):
            list_editable = "test"

        self.assertEqual(
            SongAdmin(Song, AdminSite()).check(),
            [
                checks.Error(
                    "The value of 'list_editable' must be a list or tuple.",
                    obj=SongAdmin,
                    id="admin.E120",
                )
            ],
        )