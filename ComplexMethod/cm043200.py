def _get_query_llm_config_dict(self) -> Optional[Dict]:
        """Get query LLM config as dict for chat completion calls.

        Fallback chain:
        1. self.query_llm_config (explicit query config on strategy)
        2. self.config._query_llm_config_dict (from AdaptiveConfig)
        3. self.llm_config (legacy: single config for both)
        4. None (caller uses hardcoded defaults)
        """
        # 1. Explicit query config on strategy instance
        if self.query_llm_config is not None:
            if isinstance(self.query_llm_config, dict):
                return self.query_llm_config
            return self.query_llm_config.to_dict()

        # 2. From AdaptiveConfig
        if hasattr(self, 'config') and self.config:
            config_dict = self.config._query_llm_config_dict
            if config_dict:
                return config_dict

        # 3. Legacy fallback: use embedding/shared llm_config for backward compat
        if self.llm_config is not None:
            if isinstance(self.llm_config, dict):
                return self.llm_config
            return self.llm_config.to_dict()

        # 4. None — caller applies hardcoded defaults
        return None