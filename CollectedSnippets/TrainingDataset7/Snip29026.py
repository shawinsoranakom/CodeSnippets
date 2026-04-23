def test_custom_permissions_require_matching_has_method(self):
        @admin.action(permissions=["custom"])
        def custom_permission_action(modeladmin, request, queryset):
            pass

        class BandAdmin(ModelAdmin):
            actions = (custom_permission_action,)

        self.assertIsInvalid(
            BandAdmin,
            Band,
            "BandAdmin must define a has_custom_permission() method for the "
            "custom_permission_action action.",
            id="admin.E129",
        )