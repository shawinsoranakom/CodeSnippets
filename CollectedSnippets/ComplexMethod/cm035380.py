def provider_tokens_serializer(
        self, provider_tokens: PROVIDER_TOKEN_TYPE, info: SerializationInfo
    ) -> dict[str, dict[str, str | Any]]:
        tokens = {}
        expose_secrets = info.context and info.context.get('expose_secrets', False)

        for token_type, provider_token in provider_tokens.items():
            if not provider_token or not provider_token.token:
                continue

            token_type_str = (
                token_type.value
                if isinstance(token_type, ProviderType)
                else str(token_type)
            )

            token = None
            if provider_token.token:
                token = (
                    provider_token.token.get_secret_value()
                    if expose_secrets
                    else pydantic_encoder(provider_token.token)
                )

            tokens[token_type_str] = {
                'token': token,
                'host': provider_token.host,
                'user_id': provider_token.user_id,
            }

        return tokens