def test_readonly_on_modeladmin(self):
        class SongAdmin(admin.ModelAdmin):
            readonly_fields = ("readonly_method_on_modeladmin",)

            @admin.display
            def readonly_method_on_modeladmin(self, obj):
                pass

        errors = SongAdmin(Song, AdminSite()).check()
        self.assertEqual(errors, [])