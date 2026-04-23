def test_readonly_on_method(self):
        @admin.display
        def my_function(obj):
            pass

        class SongAdmin(admin.ModelAdmin):
            readonly_fields = (my_function,)

        errors = SongAdmin(Song, AdminSite()).check()
        self.assertEqual(errors, [])