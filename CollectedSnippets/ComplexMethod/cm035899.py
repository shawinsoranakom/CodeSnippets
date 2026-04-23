def test_member_has_limited_permissions(self):
        """
        GIVEN: ROLE_PERMISSIONS mapping
        WHEN: Checking member permissions
        THEN: Member has limited permissions
        """
        member_perms = ROLE_PERMISSIONS[RoleName.MEMBER]
        # Member has basic settings permissions
        assert Permission.MANAGE_SECRETS in member_perms
        assert Permission.MANAGE_MCP in member_perms
        assert Permission.MANAGE_INTEGRATIONS in member_perms
        assert Permission.MANAGE_APPLICATION_SETTINGS in member_perms
        assert Permission.MANAGE_API_KEYS in member_perms
        assert Permission.MANAGE_AUTOMATIONS in member_perms
        assert Permission.VIEW_LLM_SETTINGS in member_perms
        assert Permission.VIEW_ORG_SETTINGS in member_perms
        # Member should NOT have admin/owner permissions
        assert Permission.EDIT_LLM_SETTINGS not in member_perms
        assert Permission.VIEW_BILLING not in member_perms
        assert Permission.ADD_CREDITS not in member_perms
        assert Permission.INVITE_USER_TO_ORGANIZATION not in member_perms
        assert Permission.CHANGE_USER_ROLE_MEMBER not in member_perms
        assert Permission.CHANGE_USER_ROLE_ADMIN not in member_perms
        assert Permission.CHANGE_USER_ROLE_OWNER not in member_perms
        assert Permission.CHANGE_ORGANIZATION_NAME not in member_perms
        assert Permission.DELETE_ORGANIZATION not in member_perms