async def test_default_values(self, sso_async_session):
        """Default values are applied when not specified."""
        config = SSOConfig(provider="oidc", provider_name="Default Test")
        sso_async_session.add(config)
        await sso_async_session.commit()
        await sso_async_session.refresh(config)

        assert config.enabled is True
        assert config.enforce_sso is False
        assert config.scopes == "openid email profile"
        assert config.email_claim == "email"
        assert config.username_claim == "preferred_username"
        assert config.user_id_claim == "sub"
        assert config.created_by is None