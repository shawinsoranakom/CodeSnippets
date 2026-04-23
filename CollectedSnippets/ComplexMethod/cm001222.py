def test_oauth2_credential_no_secret(self):
        cred = _make_oauth2_cred()
        with patch(
            "backend.api.features.integrations.router.creds_manager"
        ) as mock_mgr:
            mock_mgr.get = AsyncMock(return_value=cred)
            resp = client.get("/github/credentials/cred-456")

        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == "cred-456"
        assert data["scopes"] == ["repo", "user"]
        assert data["username"] == "testuser"
        assert "access_token" not in data
        assert "refresh_token" not in data
        assert "ghp_" not in str(data)