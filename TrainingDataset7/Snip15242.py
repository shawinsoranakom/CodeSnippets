def test_generic_inline_model_admin_non_gfk_fk_field(self):
        """
        A GenericInlineModelAdmin raises problems if the ct_fk_field points to
        a field that isn't part of a GenericForeignKey.
        """

        class InfluenceInline(GenericStackedInline):
            model = Influence
            ct_fk_field = "name"

        class SongAdmin(admin.ModelAdmin):
            inlines = [InfluenceInline]

        errors = SongAdmin(Song, AdminSite()).check()
        expected = [
            checks.Error(
                "'admin_checks.Influence' has no GenericForeignKey using "
                "content type field 'content_type' and object ID field 'name'.",
                obj=InfluenceInline,
                id="admin.E304",
            )
        ]
        self.assertEqual(errors, expected)