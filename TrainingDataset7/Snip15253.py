def test_nonexistent_field(self):
        class SongAdmin(admin.ModelAdmin):
            readonly_fields = ("title", "nonexistent")

        errors = SongAdmin(Song, AdminSite()).check()
        expected = [
            checks.Error(
                "The value of 'readonly_fields[1]' refers to 'nonexistent', which is "
                "not a callable, an attribute of 'SongAdmin', or an attribute of "
                "'admin_checks.Song'.",
                obj=SongAdmin,
                id="admin.E035",
            )
        ]
        self.assertEqual(errors, expected)