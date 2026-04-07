def test_cannot_include_through(self):
        class FieldsetBookAdmin(admin.ModelAdmin):
            fieldsets = (
                ("Header 1", {"fields": ("name",)}),
                ("Header 2", {"fields": ("authors",)}),
            )

        errors = FieldsetBookAdmin(Book, AdminSite()).check()
        expected = [
            checks.Error(
                "The value of 'fieldsets[1][1][\"fields\"]' cannot include the "
                "ManyToManyField 'authors', because that field manually specifies a "
                "relationship model.",
                obj=FieldsetBookAdmin,
                id="admin.E013",
            )
        ]
        self.assertEqual(errors, expected)