def test_admin_with_no_ordering_fallback_to_model_ordering(self):
        class NoOrderingBandAdmin(admin.ModelAdmin):
            pass

        site.register(Band, NoOrderingBandAdmin)

        # should be ordered by name (as defined by the model)
        self.check_ordering_of_field_choices([self.b2, self.b1])