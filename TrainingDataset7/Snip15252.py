def test_readonly_method_on_model(self):
        class SongAdmin(admin.ModelAdmin):
            readonly_fields = ("readonly_method_on_model",)

        errors = SongAdmin(Song, AdminSite()).check()
        self.assertEqual(errors, [])