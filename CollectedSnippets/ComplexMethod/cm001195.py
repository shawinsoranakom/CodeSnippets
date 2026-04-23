async def test_refresh_token_creates_new_tokens(
    client: httpx.AsyncClient,
    test_user: str,
    test_oauth_app: dict,
):
    """Test that refresh token grant creates new access and refresh tokens."""
    from urllib.parse import parse_qs, urlparse

    verifier, challenge = generate_pkce()

    # Get initial tokens
    auth_response = await client.post(
        "/api/oauth/authorize",
        json={
            "client_id": test_oauth_app["client_id"],
            "redirect_uri": test_oauth_app["redirect_uri"],
            "scopes": ["EXECUTE_GRAPH"],
            "state": "refresh_test",
            "response_type": "code",
            "code_challenge": challenge,
            "code_challenge_method": "S256",
        },
        follow_redirects=False,
    )

    auth_code = parse_qs(urlparse(auth_response.json()["redirect_url"]).query)["code"][
        0
    ]

    initial_response = await client.post(
        "/api/oauth/token",
        json={
            "grant_type": "authorization_code",
            "code": auth_code,
            "redirect_uri": test_oauth_app["redirect_uri"],
            "client_id": test_oauth_app["client_id"],
            "client_secret": test_oauth_app["client_secret"],
            "code_verifier": verifier,
        },
    )
    initial_tokens = initial_response.json()

    # Use refresh token to get new tokens
    refresh_response = await client.post(
        "/api/oauth/token",
        json={
            "grant_type": "refresh_token",
            "refresh_token": initial_tokens["refresh_token"],
            "client_id": test_oauth_app["client_id"],
            "client_secret": test_oauth_app["client_secret"],
        },
    )

    assert refresh_response.status_code == 200
    new_tokens = refresh_response.json()

    # Tokens should be different
    assert new_tokens["access_token"] != initial_tokens["access_token"]
    assert new_tokens["refresh_token"] != initial_tokens["refresh_token"]

    # Old refresh token should be revoked in database
    old_refresh_hash = hashlib.sha256(
        initial_tokens["refresh_token"].encode()
    ).hexdigest()
    old_db_token = await PrismaOAuthRefreshToken.prisma().find_unique(
        where={"token": old_refresh_hash}
    )
    assert old_db_token is not None
    assert old_db_token.revokedAt is not None

    # New tokens should exist and be valid
    new_access_hash = hashlib.sha256(new_tokens["access_token"].encode()).hexdigest()
    new_db_access = await PrismaOAuthAccessToken.prisma().find_unique(
        where={"token": new_access_hash}
    )
    assert new_db_access is not None
    assert new_db_access.revokedAt is None