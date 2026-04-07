def test_allows_checks_relying_on_other_modeladmins(self):
        class MyBookAdmin(admin.ModelAdmin):
            def check(self, **kwargs):
                errors = super().check(**kwargs)
                if not self.admin_site.is_registered(Author):
                    errors.append("AuthorAdmin missing!")
                return errors

        class MyAuthorAdmin(admin.ModelAdmin):
            pass

        admin.site.register(Book, MyBookAdmin)
        admin.site.register(Author, MyAuthorAdmin)
        try:
            self.assertEqual(admin.site.check(None), [])
        finally:
            admin.site.unregister(Book)
            admin.site.unregister(Author)