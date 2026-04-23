def test_nested_fieldsets(self):
        class NestedFieldsetAdmin(admin.ModelAdmin):
            fieldsets = (("Main", {"fields": ("price", ("name", "subtitle"))}),)

        errors = NestedFieldsetAdmin(Book, AdminSite()).check()
        self.assertEqual(errors, [])