def _normalize_inputs(cls, data: dict | object) -> dict | object:
        """Normalize agent_settings and secrets_store inputs."""
        if not isinstance(data, dict):
            return data

        # --- Agent settings: coerce SecretStr leaves to plain strings ---
        agent_settings = data.get('agent_settings')
        if isinstance(agent_settings, dict):
            data['agent_settings'] = _coerce_dict_secrets(agent_settings)
        elif isinstance(agent_settings, AgentSettings):
            data['agent_settings'] = agent_settings.model_dump(
                mode='json', context={'expose_secrets': True}
            )

        # --- Conversation settings: normalize ---
        conversation_settings = data.get('conversation_settings')
        if isinstance(conversation_settings, ConversationSettings):
            data['conversation_settings'] = conversation_settings.model_dump(
                mode='json'
            )

        # --- Secrets store ---
        secrets_store = data.get('secrets_store')
        if isinstance(secrets_store, dict):
            custom_secrets = secrets_store.get('custom_secrets')
            tokens = secrets_store.get('provider_tokens')
            secret_store = Secrets.model_validate(
                {'provider_tokens': {}, 'custom_secrets': {}}
            )
            if isinstance(tokens, dict):
                converted_store = Secrets.model_validate({'provider_tokens': tokens})
                secret_store = secret_store.model_copy(
                    update={'provider_tokens': converted_store.provider_tokens}
                )
            if isinstance(custom_secrets, dict):
                converted_store = Secrets.model_validate(
                    {'custom_secrets': custom_secrets}
                )
                secret_store = secret_store.model_copy(
                    update={'custom_secrets': converted_store.custom_secrets}
                )
            data['secret_store'] = secret_store

        return data