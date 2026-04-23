async def test_introspect_valid_access_token(
    client: httpx.AsyncClient,
    test_user: str,
    test_oauth_app: dict,
):
    """Test introspection returns correct info for valid access token."""
    from urllib.parse import parse_qs, urlparse

    verifier, challenge = generate_pkce()

    # Get tokens
    auth_response = await client.post(
        "/api/oauth/authorize",
        json={
            "client_id": test_oauth_app["client_id"],
            "redirect_uri": test_oauth_app["redirect_uri"],
            "scopes": ["EXECUTE_GRAPH", "READ_GRAPH"],
            "state": "introspect_test",
            "response_type": "code",
            "code_challenge": challenge,
            "code_challenge_method": "S256",
        },
        follow_redirects=False,
    )

    auth_code = parse_qs(urlparse(auth_response.json()["redirect_url"]).query)["code"][
        0
    ]

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
    tokens = token_response.json()

    # Introspect the access token
    introspect_response = await client.post(
        "/api/oauth/introspect",
        json={
            "token": tokens["access_token"],
            "token_type_hint": "access_token",
            "client_id": test_oauth_app["client_id"],
            "client_secret": test_oauth_app["client_secret"],
        },
    )

    assert introspect_response.status_code == 200
    data = introspect_response.json()

    assert data["active"] is True
    assert data["token_type"] == "access_token"
    assert data["user_id"] == test_user
    assert data["client_id"] == test_oauth_app["client_id"]
    assert "EXECUTE_GRAPH" in data["scopes"]
    assert "READ_GRAPH" in data["scopes"]