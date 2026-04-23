async def test_mixed_auth_block(self):
        """Test block that supports both OAuth2 and API key authentication."""
        # No need to import these again, already imported at top

        # Create provider supporting both auth types
        # Create provider supporting API key auth
        # In real usage, you would add OAuth support with .with_oauth()
        mixed_provider = (
            ProviderBuilder("mixed_auth_provider")
            .with_api_key("MIXED_API_KEY", "Mixed Provider API Key")
            .with_base_cost(8, BlockCostType.RUN)
            .build()
        )

        class MixedAuthBlock(Block):
            """Block supporting multiple authentication methods."""

            class Input(BlockSchemaInput):
                credentials: CredentialsMetaInput = mixed_provider.credentials_field(
                    description="API key or OAuth2 credentials",
                    supported_credential_types=["api_key", "oauth2"],
                )
                operation: str = SchemaField(description="Operation to perform")

            class Output(BlockSchemaOutput):
                result: str = SchemaField(description="Operation result")
                auth_type: str = SchemaField(description="Authentication type used")
                auth_details: dict[str, Any] = SchemaField(description="Auth details")

            def __init__(self):
                super().__init__(
                    id="mixed-auth-block",
                    description="Block supporting OAuth2 and API key",
                    categories={BlockCategory.DEVELOPER_TOOLS},
                    input_schema=MixedAuthBlock.Input,
                    output_schema=MixedAuthBlock.Output,
                )

            async def run(
                self,
                input_data: Input,
                *,
                credentials: Union[APIKeyCredentials, OAuth2Credentials],
                **kwargs,
            ) -> BlockOutput:
                # Handle different credential types
                if isinstance(credentials, APIKeyCredentials):
                    auth_type = "api_key"
                    auth_details = {
                        "has_key": bool(credentials.api_key.get_secret_value()),
                        "key_prefix": credentials.api_key.get_secret_value()[:5]
                        + "...",
                    }
                elif isinstance(credentials, OAuth2Credentials):
                    auth_type = "oauth2"
                    auth_details = {
                        "has_token": bool(credentials.access_token.get_secret_value()),
                        "scopes": credentials.scopes or [],
                    }
                else:
                    auth_type = "unknown"
                    auth_details = {}

                yield "result", f"Performed {input_data.operation} with {auth_type}"
                yield "auth_type", auth_type
                yield "auth_details", auth_details

        # Test with API key
        api_creds = APIKeyCredentials(
            id="mixed-api-creds",
            provider="mixed_auth_provider",
            api_key=SecretStr("sk-1234567890"),
            title="Mixed API Key",
        )

        block = MixedAuthBlock()
        outputs = {}
        async for name, value in block.run(
            MixedAuthBlock.Input(
                credentials={  # type: ignore
                    "provider": "mixed_auth_provider",
                    "id": "mixed-api-creds",
                    "type": "api_key",
                },
                operation="fetch_data",
            ),
            credentials=api_creds,
        ):
            outputs[name] = value

        assert outputs["auth_type"] == "api_key"
        assert outputs["result"] == "Performed fetch_data with api_key"
        assert outputs["auth_details"]["key_prefix"] == "sk-12..."

        # Test with OAuth2
        oauth_creds = OAuth2Credentials(
            id="mixed-oauth-creds",
            provider="mixed_auth_provider",
            access_token=SecretStr("oauth-token-123"),
            scopes=["full_access"],
            title="Mixed OAuth",
        )

        outputs = {}
        async for name, value in block.run(
            MixedAuthBlock.Input(
                credentials={  # type: ignore
                    "provider": "mixed_auth_provider",
                    "id": "mixed-oauth-creds",
                    "type": "oauth2",
                },
                operation="update_data",
            ),
            credentials=oauth_creds,
        ):
            outputs[name] = value

        assert outputs["auth_type"] == "oauth2"
        assert outputs["result"] == "Performed update_data with oauth2"
        assert outputs["auth_details"]["scopes"] == ["full_access"]