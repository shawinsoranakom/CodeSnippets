def test_actions_replace_global_action(self):
        @admin.action(description="Site-wide admin action 1.")
        def global_action_1(modeladmin, request, queryset):
            pass

        @admin.action(description="Site-wide admin action 2.")
        def global_action_2(modeladmin, request, queryset):
            pass

        admin.site.add_action(global_action_1, name="custom_action_1")
        admin.site.add_action(global_action_2, name="custom_action_2")

        @admin.action(description="Local admin action 1.")
        def custom_action_1(modeladmin, request, queryset):
            pass

        class BandAdmin(admin.ModelAdmin):
            actions = [custom_action_1, "custom_action_2"]

            @admin.action(description="Local admin action 2.")
            def custom_action_2(self, request, queryset):
                pass

        ma = BandAdmin(Band, admin.site)
        self.assertEqual(ma.check(), [])
        self.assertEqual(
            [
                desc
                for _, name, desc in ma._get_base_actions()
                if name.startswith("custom_action")
            ],
            [
                "Local admin action 1.",
                "Local admin action 2.",
            ],
        )