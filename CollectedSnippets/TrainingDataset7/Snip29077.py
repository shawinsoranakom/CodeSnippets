def test_raw_id_fields_widget_override(self):
        """
        The autocomplete_fields, raw_id_fields, and radio_fields widgets may
        overridden by specifying a widget in get_formset().
        """

        class ConcertInline(TabularInline):
            model = Concert
            fk_name = "main_band"
            raw_id_fields = ("opening_band",)

            def get_formset(self, request, obj=None, **kwargs):
                kwargs["widgets"] = {"opening_band": Select}
                return super().get_formset(request, obj, **kwargs)

        class BandAdmin(ModelAdmin):
            inlines = [ConcertInline]

        ma = BandAdmin(Band, self.site)
        band_widget = (
            list(ma.get_formsets_with_inlines(request))[0][0]()
            .forms[0]
            .fields["opening_band"]
            .widget
        )
        # Without the override this would be ForeignKeyRawIdWidget.
        self.assertIsInstance(band_widget, Select)