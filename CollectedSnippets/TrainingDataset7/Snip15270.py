def test_related_field_list_display_wrong_field(self):
        class SongAdmin(admin.ModelAdmin):
            list_display = ["pk", "original_release", "album__hello"]

        errors = SongAdmin(Song, AdminSite()).check()
        expected = [
            checks.Error(
                "The value of 'list_display[2]' refers to 'album__hello', which is not "
                "a callable or attribute of 'SongAdmin', or an attribute, method, or "
                "field on 'admin_checks.Song'.",
                obj=SongAdmin,
                id="admin.E108",
            )
        ]
        self.assertEqual(errors, expected)