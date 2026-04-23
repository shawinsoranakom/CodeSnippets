async def test_authorize_creates_code_in_database(
    client: httpx.AsyncClient,
    test_user: str,
    test_oauth_app: dict,
    pkce_credentials: tuple[str, str],
):
    """Test that authorization endpoint creates a code in the database."""
    verifier, challenge = pkce_credentials

    response = await client.post(
        "/api/oauth/authorize",
        json={
            "client_id": test_oauth_app["client_id"],
            "redirect_uri": test_oauth_app["redirect_uri"],
            "scopes": ["EXECUTE_GRAPH", "READ_GRAPH"],
            "state": "test_state_123",
            "response_type": "code",
            "code_challenge": challenge,
            "code_challenge_method": "S256",
        },
        follow_redirects=False,
    )

    assert response.status_code == 200
    redirect_url = response.json()["redirect_url"]

    # Parse the redirect URL to get the authorization code
    from urllib.parse import parse_qs, urlparse

    parsed = urlparse(redirect_url)
    query_params = parse_qs(parsed.query)

    assert "code" in query_params, f"Expected 'code' in query params: {query_params}"
    auth_code = query_params["code"][0]
    assert query_params["state"][0] == "test_state_123"

    # Verify code exists in database
    db_code = await PrismaOAuthAuthorizationCode.prisma().find_unique(
        where={"code": auth_code}
    )

    assert db_code is not None
    assert db_code.userId == test_user
    assert db_code.applicationId == test_oauth_app["id"]
    assert db_code.redirectUri == test_oauth_app["redirect_uri"]
    assert APIKeyPermission.EXECUTE_GRAPH in db_code.scopes
    assert APIKeyPermission.READ_GRAPH in db_code.scopes
    assert db_code.usedAt is None  # Not yet consumed
    assert db_code.codeChallenge == challenge
    assert db_code.codeChallengeMethod == "S256"