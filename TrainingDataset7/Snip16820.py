def test_formfield_overrides_for_custom_field(self):
        """
        formfield_overrides works for a custom field class.
        """

        class AlbumAdmin(admin.ModelAdmin):
            formfield_overrides = {MyFileField: {"widget": forms.TextInput()}}

        ma = AlbumAdmin(Member, admin.site)
        f1 = ma.formfield_for_dbfield(
            Album._meta.get_field("backside_art"), request=None
        )
        self.assertIsInstance(f1.widget, forms.TextInput)