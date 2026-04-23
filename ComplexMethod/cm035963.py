def _has_custom_settings(
        user_settings: UserSettings, old_user_version: int | None
    ) -> bool:
        """Check if user has custom LLM settings that should be preserved.
        Returns True if user customized either model or base_url.

        Args:
            settings: The user's current settings
            old_user_version: The user's old settings version, if any

        Returns:
            True if user has custom settings, False if using old defaults
        """
        persisted_agent_settings = user_settings.agent_settings or {}
        llm_settings = persisted_agent_settings.get('llm', {})
        if isinstance(llm_settings, dict):
            user_model = llm_settings.get('model')
            user_base_url = llm_settings.get('base_url')
        else:
            user_model = None
            user_base_url = None

        user_model = user_model.strip() or None if user_model else None
        user_base_url = user_base_url.strip() or None if user_base_url else None

        # Custom base_url = definitely custom settings (BYOK)
        if user_base_url and user_base_url != LITE_LLM_API_URL:
            return True

        # No model set = using defaults
        if not user_model:
            return False

        # Check if model matches old version's default
        if (
            old_user_version
            and old_user_version <= ORG_SETTINGS_VERSION
            and old_user_version in PERSONAL_WORKSPACE_VERSION_TO_MODEL
        ):
            old_default_base = PERSONAL_WORKSPACE_VERSION_TO_MODEL[old_user_version]
            user_model_base = user_model.split('/')[-1]
            if user_model_base == old_default_base:
                return False  # Matches old default

        return True