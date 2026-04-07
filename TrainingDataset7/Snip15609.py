def test_admin_ordering_beats_model_ordering(self):
        class StaticOrderingBandAdmin(admin.ModelAdmin):
            ordering = ("rank",)

        site.register(Band, StaticOrderingBandAdmin)

        # should be ordered by rank (defined by the ModelAdmin)
        self.check_ordering_of_field_choices([self.b1, self.b2])