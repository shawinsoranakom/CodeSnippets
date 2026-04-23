async def test_oauth_scope_validation(self):
        """Test OAuth scope validation and handling."""
        from backend.sdk import OAuth2Credentials, ProviderBuilder

        # Provider with specific required scopes
        # For testing OAuth scope validation
        scoped_provider = (
            ProviderBuilder("scoped_oauth_service")
            .with_api_key("SCOPED_OAUTH_KEY", "Scoped OAuth Service")
            .build()
        )

        class ScopeValidationBlock(Block):
            """Block that validates OAuth scopes."""

            class Input(BlockSchemaInput):
                credentials: CredentialsMetaInput = scoped_provider.credentials_field(
                    description="OAuth credentials with specific scopes",
                    scopes=["user:read", "user:write"],  # Required scopes
                )
                require_admin: bool = SchemaField(
                    description="Whether admin scopes are required",
                    default=False,
                )

            class Output(BlockSchemaOutput):
                allowed_operations: list[str] = SchemaField(
                    description="Operations allowed with current scopes"
                )
                missing_scopes: list[str] = SchemaField(
                    description="Scopes that are missing for full access"
                )
                has_required_scopes: bool = SchemaField(
                    description="Whether all required scopes are present"
                )

            def __init__(self):
                super().__init__(
                    id="scope-validation-block",
                    description="Block that validates OAuth scopes",
                    categories={BlockCategory.DEVELOPER_TOOLS},
                    input_schema=ScopeValidationBlock.Input,
                    output_schema=ScopeValidationBlock.Output,
                )

            async def run(
                self, input_data: Input, *, credentials: OAuth2Credentials, **kwargs
            ) -> BlockOutput:
                current_scopes = set(credentials.scopes or [])
                required_scopes = {"user:read", "user:write"}

                if input_data.require_admin:
                    required_scopes.update({"admin:read", "admin:write"})

                # Determine allowed operations based on scopes
                allowed_ops = []
                if "user:read" in current_scopes:
                    allowed_ops.append("read_user_data")
                if "user:write" in current_scopes:
                    allowed_ops.append("update_user_data")
                if "admin:read" in current_scopes:
                    allowed_ops.append("read_admin_data")
                if "admin:write" in current_scopes:
                    allowed_ops.append("update_admin_data")

                missing = list(required_scopes - current_scopes)
                has_required = len(missing) == 0

                yield "allowed_operations", allowed_ops
                yield "missing_scopes", missing
                yield "has_required_scopes", has_required

        # Test with partial scopes
        partial_creds = OAuth2Credentials(
            id="partial-oauth",
            provider="scoped_oauth_service",
            access_token=SecretStr("partial-token"),
            scopes=["user:read"],  # Only one of the required scopes
            title="Partial OAuth",
        )

        block = ScopeValidationBlock()
        outputs = {}
        async for name, value in block.run(
            ScopeValidationBlock.Input(
                credentials={  # type: ignore
                    "provider": "scoped_oauth_service",
                    "id": "partial-oauth",
                    "type": "oauth2",
                },
                require_admin=False,
            ),
            credentials=partial_creds,
        ):
            outputs[name] = value

        assert outputs["allowed_operations"] == ["read_user_data"]
        assert "user:write" in outputs["missing_scopes"]
        assert outputs["has_required_scopes"] is False

        # Test with all required scopes
        full_creds = OAuth2Credentials(
            id="full-oauth",
            provider="scoped_oauth_service",
            access_token=SecretStr("full-token"),
            scopes=["user:read", "user:write", "admin:read"],
            title="Full OAuth",
        )

        outputs = {}
        async for name, value in block.run(
            ScopeValidationBlock.Input(
                credentials={  # type: ignore
                    "provider": "scoped_oauth_service",
                    "id": "full-oauth",
                    "type": "oauth2",
                },
                require_admin=False,
            ),
            credentials=full_creds,
        ):
            outputs[name] = value

        assert set(outputs["allowed_operations"]) == {
            "read_user_data",
            "update_user_data",
            "read_admin_data",
        }
        assert outputs["missing_scopes"] == []
        assert outputs["has_required_scopes"] is True