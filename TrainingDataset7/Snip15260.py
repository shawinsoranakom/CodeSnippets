def test_nested_fields(self):
        class NestedFieldsAdmin(admin.ModelAdmin):
            fields = ("price", ("name", "subtitle"))

        errors = NestedFieldsAdmin(Book, AdminSite()).check()
        self.assertEqual(errors, [])