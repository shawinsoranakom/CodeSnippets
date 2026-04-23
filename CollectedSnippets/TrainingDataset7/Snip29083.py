def test_foreign_key_as_custom_widget_with_fieldset(self):
        class CustomSelectMultipleFieldset(forms.RadioSelect):
            use_fieldset = True

            def build_attrs(self, base_attrs, extra_attrs=None):
                attrs = super().build_attrs(base_attrs, extra_attrs)
                attrs["use_fieldset"] = "true"
                return attrs

        class ConcertAdmin(ModelAdmin):
            formfield_overrides = {
                models.ForeignKey: {"widget": CustomSelectMultipleFieldset},
            }

        cma = ConcertAdmin(Concert, self.site)
        cmafa = cma.get_form(request)
        expected = (
            '<fieldset><legend>Main band:</legend><div class="related-widget-wrapper" '
            'data-model-ref="band"><div id="id_main_band"><div><label '
            'for="id_main_band_0"><input type="radio" name="main_band" '
            f'value="{self.band.pk}" data-context="available-source" '
            'required id="id_main_band_0" use_fieldset="true">The Doors</label>'
            "</div></div></div></fieldset>"
        )
        self.assertInHTML(expected, cmafa().render())