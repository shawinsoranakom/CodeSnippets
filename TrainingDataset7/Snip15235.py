def test_exclude_in_inline(self):
        class ExcludedFieldsInline(admin.TabularInline):
            model = Song
            exclude = "foo"

        class ExcludedFieldsAlbumAdmin(admin.ModelAdmin):
            model = Album
            inlines = [ExcludedFieldsInline]

        errors = ExcludedFieldsAlbumAdmin(Album, AdminSite()).check()
        expected = [
            checks.Error(
                "The value of 'exclude' must be a list or tuple.",
                obj=ExcludedFieldsInline,
                id="admin.E014",
            )
        ]
        self.assertEqual(errors, expected)