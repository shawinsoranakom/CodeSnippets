def test_editable(self):
        class SongAdmin(admin.ModelAdmin):
            list_display = ["pk", "title"]
            list_editable = ["title"]
            fieldsets = [
                (
                    None,
                    {
                        "fields": ["title", "original_release"],
                    },
                ),
            ]

        errors = SongAdmin(Song, AdminSite()).check()
        self.assertEqual(errors, [])