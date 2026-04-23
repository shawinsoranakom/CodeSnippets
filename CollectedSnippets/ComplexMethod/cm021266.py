async def test_verify_redirect_uri_android_ios(client_id) -> None:
    """Test that we verify redirect uri correctly for Android/iOS."""
    with patch.object(indieauth, "fetch_redirect_uris", return_value=[]):
        assert await indieauth.verify_redirect_uri(
            None, client_id, "homeassistant://auth-callback"
        )

        assert not await indieauth.verify_redirect_uri(
            None, client_id, "homeassistant://something-else"
        )

        assert not await indieauth.verify_redirect_uri(
            None, "https://incorrect.com", "homeassistant://auth-callback"
        )

        if client_id == "https://home-assistant.io/android":
            assert await indieauth.verify_redirect_uri(
                None,
                client_id,
                "https://wear.googleapis.com/3p_auth/io.homeassistant.companion.android",
            )
            assert await indieauth.verify_redirect_uri(
                None,
                client_id,
                "https://wear.googleapis-cn.com/3p_auth/io.homeassistant.companion.android",
            )
        else:
            assert not await indieauth.verify_redirect_uri(
                None,
                client_id,
                "https://wear.googleapis.com/3p_auth/io.homeassistant.companion.android",
            )
            assert not await indieauth.verify_redirect_uri(
                None,
                client_id,
                "https://wear.googleapis-cn.com/3p_auth/io.homeassistant.companion.android",
            )