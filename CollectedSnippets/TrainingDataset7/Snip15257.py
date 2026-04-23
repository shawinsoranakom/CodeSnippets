def test_readonly_lambda(self):
        class SongAdmin(admin.ModelAdmin):
            readonly_fields = (lambda obj: "test",)

        errors = SongAdmin(Song, AdminSite()).check()
        self.assertEqual(errors, [])