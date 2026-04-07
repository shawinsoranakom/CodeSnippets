def test_get_actions_respects_permissions(self):
        class MockRequest:
            pass

        class BandAdmin(admin.ModelAdmin):
            actions = ["custom_action"]

            @admin.action
            def custom_action(modeladmin, request, queryset):
                pass

            def has_custom_permission(self, request):
                return request.user.has_perm("%s.custom_band" % self.opts.app_label)

        ma = BandAdmin(Band, admin.AdminSite())
        mock_request = MockRequest()
        mock_request.GET = {}
        cases = [
            (None, self.viewuser, ["custom_action"]),
            ("view", self.superuser, ["delete_selected", "custom_action"]),
            ("view", self.viewuser, ["custom_action"]),
            ("add", self.adduser, ["custom_action"]),
            ("change", self.changeuser, ["custom_action"]),
            ("delete", self.deleteuser, ["delete_selected", "custom_action"]),
            ("custom", self.customuser, ["custom_action"]),
        ]
        for permission, user, expected in cases:
            with self.subTest(permission=permission, user=user):
                if permission is None:
                    if hasattr(BandAdmin.custom_action, "allowed_permissions"):
                        del BandAdmin.custom_action.allowed_permissions
                else:
                    BandAdmin.custom_action.allowed_permissions = (permission,)
                mock_request.user = user
                actions = ma.get_actions(mock_request)
                self.assertEqual(list(actions.keys()), expected)