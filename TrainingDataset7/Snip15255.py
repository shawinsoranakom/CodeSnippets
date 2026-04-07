def test_readonly_fields_not_list_or_tuple(self):
        class SongAdmin(admin.ModelAdmin):
            readonly_fields = "test"

        self.assertEqual(
            SongAdmin(Song, AdminSite()).check(),
            [
                checks.Error(
                    "The value of 'readonly_fields' must be a list or tuple.",
                    obj=SongAdmin,
                    id="admin.E034",
                )
            ],
        )