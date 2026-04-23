async def test_create_and_read_sso_config(self, sso_async_session):
        """Create and read SSOConfig."""
        config = SSOConfig(
            provider="oidc",
            provider_name="Test OIDC",
        )
        sso_async_session.add(config)
        await sso_async_session.commit()
        await sso_async_session.refresh(config)

        assert config.id is not None
        assert config.provider == "oidc"
        assert config.provider_name == "Test OIDC"
        assert config.enabled is True
        assert config.enforce_sso is False
        assert config.scopes == "openid email profile"
        assert config.email_claim == "email"
        assert config.username_claim == "preferred_username"
        assert config.user_id_claim == "sub"
        assert config.created_at is not None
        assert config.updated_at is not None