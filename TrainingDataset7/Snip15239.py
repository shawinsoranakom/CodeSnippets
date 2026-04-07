def test_generic_inline_model_admin_bad_ct_field(self):
        """
        A GenericInlineModelAdmin errors if the ct_field points to a
        nonexistent field.
        """

        class InfluenceInline(GenericStackedInline):
            model = Influence
            ct_field = "nonexistent"

        class SongAdmin(admin.ModelAdmin):
            inlines = [InfluenceInline]

        errors = SongAdmin(Song, AdminSite()).check()
        expected = [
            checks.Error(
                "'ct_field' references 'nonexistent', which is not a field on "
                "'admin_checks.Influence'.",
                obj=InfluenceInline,
                id="admin.E302",
            )
        ]
        self.assertEqual(errors, expected)