async def test_revoke_token_from_different_app_fails_silently(
    client: httpx.AsyncClient,
    test_user: str,
    test_oauth_app: dict,
):
    """
    Test that an app cannot revoke tokens belonging to a different app.

    Per RFC 7009, the endpoint still returns 200 OK (to prevent token scanning),
    but the token should remain valid in the database.
    """
    from urllib.parse import parse_qs, urlparse

    verifier, challenge = generate_pkce()

    # Get tokens for app 1
    auth_response = await client.post(
        "/api/oauth/authorize",
        json={
            "client_id": test_oauth_app["client_id"],
            "redirect_uri": test_oauth_app["redirect_uri"],
            "scopes": ["EXECUTE_GRAPH"],
            "state": "cross_app_revoke_test",
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

    # Create a second OAuth app
    app2_id = str(uuid.uuid4())
    app2_client_id = f"test_client_app2_{secrets.token_urlsafe(8)}"
    app2_client_secret_plaintext = f"agpt_secret_app2_{secrets.token_urlsafe(16)}"
    app2_client_secret_hash, app2_client_secret_salt = keysmith.hash_key(
        app2_client_secret_plaintext
    )

    await PrismaOAuthApplication.prisma().create(
        data={
            "id": app2_id,
            "name": "Second Test OAuth App",
            "description": "Second test application for cross-app revocation test",
            "clientId": app2_client_id,
            "clientSecret": app2_client_secret_hash,
            "clientSecretSalt": app2_client_secret_salt,
            "redirectUris": ["https://other-app.com/callback"],
            "grantTypes": ["authorization_code", "refresh_token"],
            "scopes": [APIKeyPermission.EXECUTE_GRAPH, APIKeyPermission.READ_GRAPH],
            "ownerId": test_user,
            "isActive": True,
        }
    )

    # App 2 tries to revoke App 1's access token
    revoke_response = await client.post(
        "/api/oauth/revoke",
        json={
            "token": tokens["access_token"],
            "token_type_hint": "access_token",
            "client_id": app2_client_id,
            "client_secret": app2_client_secret_plaintext,
        },
    )

    # Per RFC 7009, returns 200 OK even if token not found/not owned
    assert revoke_response.status_code == 200
    assert revoke_response.json()["status"] == "ok"

    # But the token should NOT be revoked in the database
    access_hash = hashlib.sha256(tokens["access_token"].encode()).hexdigest()
    db_token = await PrismaOAuthAccessToken.prisma().find_unique(
        where={"token": access_hash}
    )
    assert db_token is not None
    assert db_token.revokedAt is None, "Token should NOT be revoked by different app"

    # Now app 1 revokes its own token - should work
    revoke_response2 = await client.post(
        "/api/oauth/revoke",
        json={
            "token": tokens["access_token"],
            "token_type_hint": "access_token",
            "client_id": test_oauth_app["client_id"],
            "client_secret": test_oauth_app["client_secret"],
        },
    )

    assert revoke_response2.status_code == 200

    # Token should now be revoked
    db_token_after = await PrismaOAuthAccessToken.prisma().find_unique(
        where={"token": access_hash}
    )
    assert db_token_after is not None
    assert db_token_after.revokedAt is not None, "Token should be revoked by own app"

    # Cleanup second app
    await PrismaOAuthApplication.prisma().delete(where={"id": app2_id})