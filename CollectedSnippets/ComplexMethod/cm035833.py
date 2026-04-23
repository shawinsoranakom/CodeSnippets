def get_config(self):
        # These providers are configurable via helm charts for self hosted deployments
        # The FE should have this info so that the login buttons reflect the supported IDPs
        providers_configured = []
        if GITHUB_APP_CLIENT_ID:
            providers_configured.append(ProviderType.GITHUB)

        if GITLAB_APP_CLIENT_ID:
            providers_configured.append(ProviderType.GITLAB)

        if BITBUCKET_APP_CLIENT_ID:
            providers_configured.append(ProviderType.BITBUCKET)

        if ENABLE_ENTERPRISE_SSO:
            providers_configured.append(ProviderType.ENTERPRISE_SSO)

        if BITBUCKET_DATA_CENTER_CLIENT_ID:
            providers_configured.append(ProviderType.BITBUCKET_DATA_CENTER)

        config: dict[str, typing.Any] = {
            'APP_MODE': self.app_mode,
            'APP_SLUG': self.app_slug,
            'GITHUB_CLIENT_ID': self.github_client_id,
            'POSTHOG_CLIENT_KEY': self.posthog_client_key,
            'FEATURE_FLAGS': {
                'ENABLE_BILLING': self.enable_billing,
                'HIDE_LLM_SETTINGS': self.hide_llm_settings,
                'ENABLE_JIRA': self.enable_jira,
                'ENABLE_JIRA_DC': self.enable_jira_dc,
                'ENABLE_LINEAR': self.enable_linear,
                'DEPLOYMENT_MODE': DEPLOYMENT_MODE,
            },
            'PROVIDERS_CONFIGURED': providers_configured,
        }

        # Add maintenance window if configured
        if self.maintenance_start_time:
            config['MAINTENANCE'] = {
                'startTime': self.maintenance_start_time,
            }

        if self.auth_url:
            config['AUTH_URL'] = self.auth_url

        if RECAPTCHA_SITE_KEY:
            config['RECAPTCHA_SITE_KEY'] = RECAPTCHA_SITE_KEY

        return config