def test_global_actions_description(self):
        @admin.action(description="Site-wide admin action 1.")
        def global_action_1(modeladmin, request, queryset):
            pass

        @admin.action
        def global_action_2(modeladmin, request, queryset):
            pass

        admin_site = admin.AdminSite()
        admin_site.add_action(global_action_1)
        admin_site.add_action(global_action_2)

        class BandAdmin(admin.ModelAdmin):
            pass

        ma = BandAdmin(Band, admin_site)
        self.assertEqual(
            [description for _, _, description in ma._get_base_actions()],
            [
                "Delete selected %(verbose_name_plural)s",
                "Site-wide admin action 1.",
                "Global action 2",
            ],
        )