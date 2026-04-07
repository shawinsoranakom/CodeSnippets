def test_formset_exclude_kwarg_override(self):
        """
        The `exclude` kwarg passed to `InlineModelAdmin.get_formset()`
        overrides all other declarations (#8999).
        """

        class AdminConcertForm(forms.ModelForm):
            class Meta:
                model = Concert
                exclude = ["day"]

        class ConcertInline(TabularInline):
            exclude = ["transport"]
            form = AdminConcertForm
            fk_name = "main_band"
            model = Concert

            def get_formset(self, request, obj=None, **kwargs):
                kwargs["exclude"] = ["opening_band"]
                return super().get_formset(request, obj, **kwargs)

        class BandAdmin(ModelAdmin):
            inlines = [ConcertInline]

        ma = BandAdmin(Band, self.site)
        self.assertEqual(
            list(list(ma.get_formsets_with_inlines(request))[0][0]().forms[0].fields),
            ["main_band", "day", "transport", "id", "DELETE"],
        )