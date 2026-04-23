def convert_dict_to_mappingproxy(
        cls, data: dict[str, dict[str, Any] | MappingProxyType] | PROVIDER_TOKEN_TYPE
    ) -> dict[str, MappingProxyType | None]:
        """Custom deserializer to convert dictionary into MappingProxyType"""
        if not isinstance(data, dict):
            raise ValueError('Secrets must be initialized with a dictionary')

        new_data: dict[str, MappingProxyType | None] = {}

        if 'provider_tokens' in data:
            tokens = data['provider_tokens']
            if isinstance(
                tokens, dict
            ):  # Ensure conversion happens only for dict inputs
                converted_tokens = {}
                for key, value in tokens.items():
                    try:
                        provider_type = (
                            ProviderType(key) if isinstance(key, str) else key
                        )
                        converted_tokens[provider_type] = ProviderToken.from_value(
                            value
                        )
                    except ValueError:
                        # Skip invalid provider types or tokens
                        continue

                # Convert to MappingProxyType
                new_data['provider_tokens'] = MappingProxyType(converted_tokens)
            elif isinstance(tokens, MappingProxyType):
                new_data['provider_tokens'] = tokens

        if 'custom_secrets' in data:
            secrets = data['custom_secrets']
            if isinstance(secrets, dict):
                converted_secrets = {}
                for key, value in secrets.items():
                    try:
                        converted_secrets[key] = CustomSecret.from_value(value)
                    except ValueError:
                        continue

                new_data['custom_secrets'] = MappingProxyType(converted_secrets)
            elif isinstance(secrets, MappingProxyType):
                new_data['custom_secrets'] = secrets

        return new_data