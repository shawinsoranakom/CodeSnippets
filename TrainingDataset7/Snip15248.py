def test_readonly(self):
        class SongAdmin(admin.ModelAdmin):
            readonly_fields = ("title",)

        errors = SongAdmin(Song, AdminSite()).check()
        self.assertEqual(errors, [])