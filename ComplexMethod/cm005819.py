async def test_create_and_read_sso_user_profile(self, sso_async_session):
        """Create and read SSOUserProfile records."""
        user = User(username="sso_user", password=_TEST_PASSWORD)
        sso_async_session.add(user)
        await sso_async_session.commit()
        await sso_async_session.refresh(user)

        profile = SSOUserProfile(
            user_id=user.id,
            sso_provider="oidc",
            sso_user_id="sub-123",
            email="user@example.com",
        )
        sso_async_session.add(profile)
        await sso_async_session.commit()
        await sso_async_session.refresh(profile)

        assert profile.id is not None
        assert profile.user_id == user.id
        assert profile.sso_provider == "oidc"
        assert profile.sso_user_id == "sub-123"
        assert profile.email == "user@example.com"
        assert profile.created_at is not None
        assert profile.updated_at is not None