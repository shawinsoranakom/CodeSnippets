def test_actions_not_unique(self):
        @admin.action
        def action(modeladmin, request, queryset):
            pass

        class BandAdmin(ModelAdmin):
            actions = (action, action)

        self.assertIsInvalid(
            BandAdmin,
            Band,
            "__name__ attributes of actions defined in BandAdmin must be "
            "unique. Name 'action' is not unique.",
            id="admin.E130",
        )