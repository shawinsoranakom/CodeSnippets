def test_foreign_key_as_custom_widget(self):
        class CustomSelectMultiple(forms.SelectMultiple):
            def build_attrs(self, base_attrs, extra_attrs=None):
                attrs = super().build_attrs(base_attrs, extra_attrs)
                attrs["data-custom-widget"] = "true"
                return attrs

        class ConcertAdmin(ModelAdmin):
            formfield_overrides = {
                models.ForeignKey: {"widget": CustomSelectMultiple},
            }

        cma = ConcertAdmin(Concert, self.site)
        cmafa = cma.get_form(request)
        expected = (
            '<div><label for="id_main_band">Main band:</label><div '
            'class="related-widget-wrapper" data-model-ref="band"><select '
            'name="main_band" data-context="available-source" required '
            'id="id_main_band" data-custom-widget="true" multiple>'
            '<option value="">---------</option>'
            f'<option value="{self.band.pk}">The Doors</option>'
            "</select></div></div>"
        )
        self.assertInHTML(expected, cmafa().render())