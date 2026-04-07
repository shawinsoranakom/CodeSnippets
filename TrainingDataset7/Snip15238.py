def test_generic_inline_model_admin_non_generic_model(self):
        """
        A model without a GenericForeignKey raises problems if it's included
        in a GenericInlineModelAdmin definition.
        """

        class BookInline(GenericStackedInline):
            model = Book

        class SongAdmin(admin.ModelAdmin):
            inlines = [BookInline]

        errors = SongAdmin(Song, AdminSite()).check()
        expected = [
            checks.Error(
                "'admin_checks.Book' has no GenericForeignKey.",
                obj=BookInline,
                id="admin.E301",
            )
        ]
        self.assertEqual(errors, expected)