def test_inlines_property(self):
        class CitiesInline(admin.TabularInline):
            model = City

        class StateAdmin(admin.ModelAdmin):
            @property
            def inlines(self):
                return [CitiesInline]

        errors = StateAdmin(State, AdminSite()).check()
        self.assertEqual(errors, [])