def test_generic_inline_model_admin_non_gfk_ct_field(self):
        """
        A GenericInlineModelAdmin raises problems if the ct_field points to a
        field that isn't part of a GenericForeignKey.
        """

        class InfluenceInline(GenericStackedInline):
            model = Influence
            ct_field = "name"

        class SongAdmin(admin.ModelAdmin):
            inlines = [InfluenceInline]

        errors = SongAdmin(Song, AdminSite()).check()
        expected = [
            checks.Error(
                "'admin_checks.Influence' has no GenericForeignKey using "
                "content type field 'name' and object ID field 'object_id'.",
                obj=InfluenceInline,
                id="admin.E304",
            )
        ]
        self.assertEqual(errors, expected)