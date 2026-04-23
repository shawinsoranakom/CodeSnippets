def test_admin_has_admin_permissions(self):
        """
        GIVEN: ROLE_PERMISSIONS mapping
        WHEN: Checking admin permissions
        THEN: Admin has admin permissions but not owner-only permissions
        """
        admin_perms = ROLE_PERMISSIONS[RoleName.ADMIN]
        assert Permission.MANAGE_SECRETS in admin_perms
        assert Permission.MANAGE_MCP in admin_perms
        assert Permission.VIEW_LLM_SETTINGS in admin_perms
        assert Permission.EDIT_LLM_SETTINGS in admin_perms
        assert Permission.VIEW_BILLING in admin_perms
        assert Permission.ADD_CREDITS in admin_perms
        assert Permission.INVITE_USER_TO_ORGANIZATION in admin_perms
        assert Permission.CHANGE_USER_ROLE_MEMBER in admin_perms
        assert Permission.CHANGE_USER_ROLE_ADMIN in admin_perms
        assert Permission.MANAGE_AUTOMATIONS in admin_perms
        # Admin should NOT have owner-only permissions
        assert Permission.CHANGE_USER_ROLE_OWNER not in admin_perms
        assert Permission.CHANGE_ORGANIZATION_NAME not in admin_perms
        assert Permission.DELETE_ORGANIZATION not in admin_perms