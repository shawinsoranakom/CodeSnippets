def test_list_credentials_includes_is_managed_field(self):
        managed = APIKeyCredentials(
            id="managed-1",
            provider="agent_mail",
            title="AgentMail (managed)",
            api_key=SecretStr("sk-key"),
            is_managed=True,
        )
        regular = APIKeyCredentials(
            id="regular-1",
            provider="openai",
            title="My Key",
            api_key=SecretStr("sk-key"),
        )
        with patch(
            "backend.api.features.integrations.router.creds_manager"
        ) as mock_mgr:
            mock_mgr.store.get_all_creds = AsyncMock(return_value=[managed, regular])
            resp = client.get("/credentials")

        assert resp.status_code == 200
        data = resp.json()
        managed_cred = next(c for c in data if c["id"] == "managed-1")
        regular_cred = next(c for c in data if c["id"] == "regular-1")
        assert managed_cred["is_managed"] is True
        assert regular_cred["is_managed"] is False