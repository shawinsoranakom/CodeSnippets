def test_generic_inline_model_admin_bad_fk_field(self):
        """
        A GenericInlineModelAdmin errors if the ct_fk_field points to a
        nonexistent field.
        """

        class InfluenceInline(GenericStackedInline):
            model = Influence
            ct_fk_field = "nonexistent"

        class SongAdmin(admin.ModelAdmin):
            inlines = [InfluenceInline]

        errors = SongAdmin(Song, AdminSite()).check()
        expected = [
            checks.Error(
                "'ct_fk_field' references 'nonexistent', which is not a field on "
                "'admin_checks.Influence'.",
                obj=InfluenceInline,
                id="admin.E303",
            )
        ]
        self.assertEqual(errors, expected)