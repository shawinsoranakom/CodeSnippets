def test_m2m_widgets(self):
        """m2m fields help text as it applies to admin app (#9321)."""

        class AdvisorAdmin(admin.ModelAdmin):
            filter_vertical = ["companies"]

        self.assertFormfield(
            Advisor,
            "companies",
            widgets.FilteredSelectMultiple,
            filter_vertical=["companies"],
        )
        ma = AdvisorAdmin(Advisor, admin.site)
        f = ma.formfield_for_dbfield(Advisor._meta.get_field("companies"), request=None)
        self.assertEqual(
            f.help_text,
            "Hold down “Control”, or “Command” on a Mac, to select more than one.",
        )