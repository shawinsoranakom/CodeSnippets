def test_permission_values(self):
        """
        GIVEN: Permission enum
        WHEN: Accessing permission values
        THEN: All expected permissions exist with correct string values
        """
        assert Permission.MANAGE_SECRETS.value == 'manage_secrets'
        assert Permission.MANAGE_MCP.value == 'manage_mcp'
        assert Permission.MANAGE_INTEGRATIONS.value == 'manage_integrations'
        assert (
            Permission.MANAGE_APPLICATION_SETTINGS.value
            == 'manage_application_settings'
        )
        assert Permission.MANAGE_API_KEYS.value == 'manage_api_keys'
        assert Permission.VIEW_LLM_SETTINGS.value == 'view_llm_settings'
        assert Permission.EDIT_LLM_SETTINGS.value == 'edit_llm_settings'
        assert Permission.VIEW_BILLING.value == 'view_billing'
        assert Permission.ADD_CREDITS.value == 'add_credits'
        assert (
            Permission.INVITE_USER_TO_ORGANIZATION.value
            == 'invite_user_to_organization'
        )
        assert Permission.CHANGE_USER_ROLE_MEMBER.value == 'change_user_role:member'
        assert Permission.CHANGE_USER_ROLE_ADMIN.value == 'change_user_role:admin'
        assert Permission.CHANGE_USER_ROLE_OWNER.value == 'change_user_role:owner'
        assert Permission.VIEW_ORG_SETTINGS.value == 'view_org_settings'
        assert Permission.CHANGE_ORGANIZATION_NAME.value == 'change_organization_name'
        assert Permission.DELETE_ORGANIZATION.value == 'delete_organization'
        assert Permission.MANAGE_AUTOMATIONS.value == 'manage_automations'