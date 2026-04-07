def test_valid_generic_inline_model_admin(self):
        """
        Regression test for #22034 - check that generic inlines don't look for
        normal ForeignKey relations.
        """

        class InfluenceInline(GenericStackedInline):
            model = Influence

        class SongAdmin(admin.ModelAdmin):
            inlines = [InfluenceInline]

        errors = SongAdmin(Song, AdminSite()).check()
        self.assertEqual(errors, [])