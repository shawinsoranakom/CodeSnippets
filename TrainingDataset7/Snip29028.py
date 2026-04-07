def test_actions_unique(self):
        @admin.action
        def action1(modeladmin, request, queryset):
            pass

        @admin.action
        def action2(modeladmin, request, queryset):
            pass

        class BandAdmin(ModelAdmin):
            actions = (action1, action2)

        self.assertIsValid(BandAdmin, Band)