def test_actions_inheritance(self):
        class AdminBase(admin.ModelAdmin):
            actions = ["custom_action"]

            @admin.action
            def custom_action(modeladmin, request, queryset):
                pass

        class AdminA(AdminBase):
            pass

        class AdminB(AdminBase):
            actions = None

        ma1 = AdminA(Band, admin.AdminSite())
        action_names = [name for _, name, _ in ma1._get_base_actions()]
        self.assertEqual(action_names, ["delete_selected", "custom_action"])
        # `actions = None` removes actions from superclasses.
        ma2 = AdminB(Band, admin.AdminSite())
        action_names = [name for _, name, _ in ma2._get_base_actions()]
        self.assertEqual(action_names, ["delete_selected"])