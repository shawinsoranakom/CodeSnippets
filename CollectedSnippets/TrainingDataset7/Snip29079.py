def test_regression_for_ticket_15820(self):
        """
        `obj` is passed from `InlineModelAdmin.get_fieldsets()` to
        `InlineModelAdmin.get_formset()`.
        """

        class CustomConcertForm(forms.ModelForm):
            class Meta:
                model = Concert
                fields = ["day"]

        class ConcertInline(TabularInline):
            model = Concert
            fk_name = "main_band"

            def get_formset(self, request, obj=None, **kwargs):
                if obj:
                    kwargs["form"] = CustomConcertForm
                return super().get_formset(request, obj, **kwargs)

        class BandAdmin(ModelAdmin):
            inlines = [ConcertInline]

        Concert.objects.create(main_band=self.band, opening_band=self.band, day=1)
        ma = BandAdmin(Band, self.site)
        inline_instances = ma.get_inline_instances(request)
        fieldsets = list(inline_instances[0].get_fieldsets(request))
        self.assertEqual(
            fieldsets[0][1]["fields"], ["main_band", "opening_band", "day", "transport"]
        )
        fieldsets = list(
            inline_instances[0].get_fieldsets(request, inline_instances[0].model)
        )
        self.assertEqual(fieldsets[0][1]["fields"], ["day"])