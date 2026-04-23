def test_readonly_and_editable(self):
        class SongAdmin(admin.ModelAdmin):
            readonly_fields = ["original_release"]
            list_display = ["pk", "original_release"]
            list_editable = ["original_release"]
            fieldsets = [
                (
                    None,
                    {
                        "fields": ["title", "original_release"],
                    },
                ),
            ]

        errors = SongAdmin(Song, AdminSite()).check()
        expected = [
            checks.Error(
                "The value of 'list_editable[0]' refers to 'original_release', "
                "which is not editable through the admin.",
                obj=SongAdmin,
                id="admin.E125",
            )
        ]
        self.assertEqual(errors, expected)