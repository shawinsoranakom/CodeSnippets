def test_default_fieldsets(self):
        # fieldsets_add and fieldsets_change should return a special data
        # structure that is used in the templates. They should generate the
        # "right thing" whether we have specified a custom form, the fields
        # argument, or nothing at all.
        #
        # Here's the default case. There are no custom form_add/form_change
        # methods, no fields argument, and no fieldsets argument.
        ma = ModelAdmin(Band, self.site)
        self.assertEqual(
            ma.get_fieldsets(request),
            [(None, {"fields": ["name", "bio", "sign_date"]})],
        )
        self.assertEqual(
            ma.get_fieldsets(request, self.band),
            [(None, {"fields": ["name", "bio", "sign_date"]})],
        )