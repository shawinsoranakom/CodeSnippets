def update(self, payload: dict[str, Any]) -> None:
        """Apply a batch of changes from a nested dict.

        ``agent_settings_diff`` and ``conversation_settings_diff`` use nested
        dict shape (matching model_dump). Top-level keys are set directly on the
        model.
        """
        legacy_nested_keys = [
            key for key in ('agent_settings', 'conversation_settings') if key in payload
        ]
        if legacy_nested_keys:
            raise ValueError(
                'Use *_diff nested settings payloads instead of legacy '
                + ', '.join(sorted(legacy_nested_keys))
            )

        agent_update = payload.get('agent_settings_diff')
        if isinstance(agent_update, dict):
            coerced: dict[str, Any] = {}
            for key, value in agent_update.items():
                coerced[key] = (
                    _coerce_value(value) if not isinstance(value, dict) else value
                )

            replace_mcp_config = 'mcp_config' in agent_update
            mcp_config = coerced.pop('mcp_config', None) if replace_mcp_config else None

            merged = deep_merge(
                self.agent_settings.model_dump(
                    mode='json', context={'expose_secrets': True}
                ),
                coerced,
            )
            if replace_mcp_config:
                merged['mcp_config'] = mcp_config

            # Use object.__setattr__ to avoid validate_assignment
            # side-effects on other fields.
            object.__setattr__(
                self, 'agent_settings', AgentSettings.model_validate(merged)
            )

        conv_update = payload.get('conversation_settings_diff')
        if isinstance(conv_update, dict):
            merged = deep_merge(
                self.conversation_settings.model_dump(mode='json'),
                conv_update,
            )
            object.__setattr__(
                self,
                'conversation_settings',
                ConversationSettings.model_validate(merged),
            )

        for key, value in payload.items():
            if key in ('agent_settings_diff', 'conversation_settings_diff'):
                continue
            if key in Settings.model_fields and key not in _SETTINGS_FROZEN_FIELDS:
                field_info = Settings.model_fields[key]
                # Coerce plain strings to SecretStr when the field type expects it
                if value is not None and isinstance(value, str):
                    annotation = field_info.annotation
                    if annotation is SecretStr or (
                        hasattr(annotation, '__args__')
                        and SecretStr in getattr(annotation, '__args__', ())
                    ):
                        value = SecretStr(value) if value else None
                setattr(self, key, value)