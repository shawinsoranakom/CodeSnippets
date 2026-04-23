def test_owner_has_all_permissions(self):
        """
        GIVEN: ROLE_PERMISSIONS mapping
        WHEN: Checking owner permissions
        THEN: Owner has all permissions including owner-only permissions
        """
        owner_perms = ROLE_PERMISSIONS[RoleName.OWNER]
        assert Permission.MANAGE_SECRETS in owner_perms
        assert Permission.MANAGE_MCP in owner_perms
        assert Permission.VIEW_LLM_SETTINGS in owner_perms
        assert Permission.EDIT_LLM_SETTINGS in owner_perms
        assert Permission.VIEW_BILLING in owner_perms
        assert Permission.ADD_CREDITS in owner_perms
        assert Permission.INVITE_USER_TO_ORGANIZATION in owner_perms
        assert Permission.CHANGE_USER_ROLE_MEMBER in owner_perms
        assert Permission.CHANGE_USER_ROLE_ADMIN in owner_perms
        assert Permission.CHANGE_USER_ROLE_OWNER in owner_perms
        assert Permission.CHANGE_ORGANIZATION_NAME in owner_perms
        assert Permission.DELETE_ORGANIZATION in owner_perms
        assert Permission.MANAGE_AUTOMATIONS in owner_perms