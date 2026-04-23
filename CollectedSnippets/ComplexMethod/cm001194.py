async def test_token_exchange_creates_tokens_in_database(
    client: httpx.AsyncClient,
    test_user: str,
    test_oauth_app: dict,
):
    """Test that token exchange creates access and refresh tokens in database."""
    from urllib.parse import parse_qs, urlparse

    verifier, challenge = generate_pkce()

    # First get an authorization code
    auth_response = await client.post(
        "/api/oauth/authorize",
        json={
            "client_id": test_oauth_app["client_id"],
            "redirect_uri": test_oauth_app["redirect_uri"],
            "scopes": ["EXECUTE_GRAPH", "READ_GRAPH"],
            "state": "token_test_state",
            "response_type": "code",
            "code_challenge": challenge,
            "code_challenge_method": "S256",
        },
        follow_redirects=False,
    )

    auth_code = parse_qs(urlparse(auth_response.json()["redirect_url"]).query)["code"][
        0
    ]

    # Exchange code for tokens
    token_response = await client.post(
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

    assert token_response.status_code == 200
    tokens = token_response.json()

    assert "access_token" in tokens
    assert "refresh_token" in tokens
    assert tokens["token_type"] == "Bearer"
    assert "EXECUTE_GRAPH" in tokens["scopes"]
    assert "READ_GRAPH" in tokens["scopes"]

    # Verify access token exists in database (hashed)
    access_token_hash = hashlib.sha256(tokens["access_token"].encode()).hexdigest()
    db_access_token = await PrismaOAuthAccessToken.prisma().find_unique(
        where={"token": access_token_hash}
    )

    assert db_access_token is not None
    assert db_access_token.userId == test_user
    assert db_access_token.applicationId == test_oauth_app["id"]
    assert db_access_token.revokedAt is None

    # Verify refresh token exists in database (hashed)
    refresh_token_hash = hashlib.sha256(tokens["refresh_token"].encode()).hexdigest()
    db_refresh_token = await PrismaOAuthRefreshToken.prisma().find_unique(
        where={"token": refresh_token_hash}
    )

    assert db_refresh_token is not None
    assert db_refresh_token.userId == test_user
    assert db_refresh_token.applicationId == test_oauth_app["id"]
    assert db_refresh_token.revokedAt is None

    # Verify authorization code is marked as used
    db_code = await PrismaOAuthAuthorizationCode.prisma().find_unique(
        where={"code": auth_code}
    )
    assert db_code is not None
    assert db_code.usedAt is not None