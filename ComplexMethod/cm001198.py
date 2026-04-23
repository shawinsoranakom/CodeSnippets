async def test_complete_oauth_flow_end_to_end(
    client: httpx.AsyncClient,
    test_user: str,
    test_oauth_app: dict,
    pkce_credentials: tuple[str, str],
):
    """
    Test the complete OAuth 2.0 flow from authorization to token refresh.

    This is a comprehensive integration test that verifies the entire
    OAuth flow works correctly with real API calls and database operations.
    """
    from urllib.parse import parse_qs, urlparse

    verifier, challenge = pkce_credentials

    # Step 1: Authorization request with PKCE
    auth_response = await client.post(
        "/api/oauth/authorize",
        json={
            "client_id": test_oauth_app["client_id"],
            "redirect_uri": test_oauth_app["redirect_uri"],
            "scopes": ["EXECUTE_GRAPH", "READ_GRAPH"],
            "state": "e2e_test_state",
            "response_type": "code",
            "code_challenge": challenge,
            "code_challenge_method": "S256",
        },
        follow_redirects=False,
    )

    assert auth_response.status_code == 200

    redirect_url = auth_response.json()["redirect_url"]
    query = parse_qs(urlparse(redirect_url).query)

    assert query["state"][0] == "e2e_test_state"
    auth_code = query["code"][0]

    # Verify authorization code in database
    db_code = await PrismaOAuthAuthorizationCode.prisma().find_unique(
        where={"code": auth_code}
    )
    assert db_code is not None
    assert db_code.codeChallenge == challenge

    # Step 2: Exchange code for tokens
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

    # Verify code is marked as used
    db_code_used = await PrismaOAuthAuthorizationCode.prisma().find_unique_or_raise(
        where={"code": auth_code}
    )
    assert db_code_used.usedAt is not None

    # Step 3: Introspect access token
    introspect_response = await client.post(
        "/api/oauth/introspect",
        json={
            "token": tokens["access_token"],
            "client_id": test_oauth_app["client_id"],
            "client_secret": test_oauth_app["client_secret"],
        },
    )

    assert introspect_response.status_code == 200
    introspect_data = introspect_response.json()
    assert introspect_data["active"] is True
    assert introspect_data["user_id"] == test_user

    # Step 4: Refresh tokens
    refresh_response = await client.post(
        "/api/oauth/token",
        json={
            "grant_type": "refresh_token",
            "refresh_token": tokens["refresh_token"],
            "client_id": test_oauth_app["client_id"],
            "client_secret": test_oauth_app["client_secret"],
        },
    )

    assert refresh_response.status_code == 200
    new_tokens = refresh_response.json()
    assert new_tokens["access_token"] != tokens["access_token"]
    assert new_tokens["refresh_token"] != tokens["refresh_token"]

    # Verify old refresh token is revoked
    old_refresh_hash = hashlib.sha256(tokens["refresh_token"].encode()).hexdigest()
    old_db_refresh = await PrismaOAuthRefreshToken.prisma().find_unique_or_raise(
        where={"token": old_refresh_hash}
    )
    assert old_db_refresh.revokedAt is not None

    # Step 5: Verify new access token works
    new_introspect = await client.post(
        "/api/oauth/introspect",
        json={
            "token": new_tokens["access_token"],
            "client_id": test_oauth_app["client_id"],
            "client_secret": test_oauth_app["client_secret"],
        },
    )

    assert new_introspect.status_code == 200
    assert new_introspect.json()["active"] is True

    # Step 6: Revoke new access token
    revoke_response = await client.post(
        "/api/oauth/revoke",
        json={
            "token": new_tokens["access_token"],
            "token_type_hint": "access_token",
            "client_id": test_oauth_app["client_id"],
            "client_secret": test_oauth_app["client_secret"],
        },
    )

    assert revoke_response.status_code == 200

    # Step 7: Verify revoked token is inactive
    final_introspect = await client.post(
        "/api/oauth/introspect",
        json={
            "token": new_tokens["access_token"],
            "client_id": test_oauth_app["client_id"],
            "client_secret": test_oauth_app["client_secret"],
        },
    )

    assert final_introspect.status_code == 200
    assert final_introspect.json()["active"] is False

    # Verify in database
    new_access_hash = hashlib.sha256(new_tokens["access_token"].encode()).hexdigest()
    db_revoked = await PrismaOAuthAccessToken.prisma().find_unique_or_raise(
        where={"token": new_access_hash}
    )
    assert db_revoked.revokedAt is not None