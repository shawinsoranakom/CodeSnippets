def test_m2m_widgets_no_allow_multiple_selected(self):
        class NoAllowMultipleSelectedWidget(forms.SelectMultiple):
            allow_multiple_selected = False

        class AdvisorAdmin(admin.ModelAdmin):
            filter_vertical = ["companies"]
            formfield_overrides = {
                ManyToManyField: {"widget": NoAllowMultipleSelectedWidget},
            }

        self.assertFormfield(
            Advisor,
            "companies",
            widgets.FilteredSelectMultiple,
            filter_vertical=["companies"],
        )
        ma = AdvisorAdmin(Advisor, admin.site)
        f = ma.formfield_for_dbfield(Advisor._meta.get_field("companies"), request=None)
        self.assertEqual(f.help_text, "")