def test_queryset_override(self):
        # If the queryset of a ModelChoiceField in a custom form is overridden,
        # RelatedFieldWidgetWrapper doesn't mess that up.
        band2 = Band.objects.create(
            name="The Beatles", bio="", sign_date=date(1962, 1, 1)
        )

        ma = ModelAdmin(Concert, self.site)
        form = ma.get_form(request)()

        self.assertHTMLEqual(
            str(form["main_band"]),
            '<div class="related-widget-wrapper" data-model-ref="band">'
            '<select data-context="available-source" '
            'name="main_band" id="id_main_band" required>'
            '<option value="" selected>---------</option>'
            '<option value="%s">The Beatles</option>'
            '<option value="%s">The Doors</option>'
            "</select></div>" % (band2.id, self.band.id),
        )

        class AdminConcertForm(forms.ModelForm):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.fields["main_band"].queryset = Band.objects.filter(
                    name="The Doors"
                )

        class ConcertAdminWithForm(ModelAdmin):
            form = AdminConcertForm

        ma = ConcertAdminWithForm(Concert, self.site)
        form = ma.get_form(request)()

        self.assertHTMLEqual(
            str(form["main_band"]),
            '<div class="related-widget-wrapper" data-model-ref="band">'
            '<select data-context="available-source" '
            'name="main_band" id="id_main_band" required>'
            '<option value="" selected>---------</option>'
            '<option value="%s">The Doors</option>'
            "</select></div>" % self.band.id,
        )