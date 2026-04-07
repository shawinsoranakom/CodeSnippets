def test_related_field_list_display(self):
        class SongAdmin(admin.ModelAdmin):
            list_display = ["pk", "original_release", "album__title"]

        errors = SongAdmin(Song, AdminSite()).check()
        self.assertEqual(errors, [])