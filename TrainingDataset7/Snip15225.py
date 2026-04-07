def test_list_editable_missing_field(self):
        class SongAdmin(admin.ModelAdmin):
            list_editable = ("test",)

        self.assertEqual(
            SongAdmin(Song, AdminSite()).check(),
            [
                checks.Error(
                    "The value of 'list_editable[0]' refers to 'test', which is "
                    "not a field of 'admin_checks.Song'.",
                    obj=SongAdmin,
                    id="admin.E121",
                )
            ],
        )