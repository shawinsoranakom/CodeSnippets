def test_readonly_dynamic_attribute_on_modeladmin(self):
        class SongAdmin(admin.ModelAdmin):
            readonly_fields = ("dynamic_method",)

            def __getattr__(self, item):
                if item == "dynamic_method":

                    @admin.display
                    def method(obj):
                        pass

                    return method
                raise AttributeError

        errors = SongAdmin(Song, AdminSite()).check()
        self.assertEqual(errors, [])