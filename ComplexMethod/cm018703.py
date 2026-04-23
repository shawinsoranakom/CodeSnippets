async def complete_external_step(
        self, result: data_entry_flow.FlowResult
    ) -> data_entry_flow.FlowResult:
        """Fixture method to complete the OAuth flow and return the completed result."""
        client = await self.hass_client()
        state = config_entry_oauth2_flow._encode_jwt(
            self.hass,
            {
                "flow_id": result["flow_id"],
                "redirect_uri": "https://example.com/auth/external/callback",
            },
        )
        assert result["url"] == (
            f"{AUTHORIZE_URL}?response_type=code&client_id={self.client_id}"
            "&redirect_uri=https://example.com/auth/external/callback"
            f"&state={state}"
        )
        resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
        assert resp.status == 200
        assert resp.headers["content-type"] == "text/html; charset=utf-8"

        self.aioclient_mock.post(
            TOKEN_URL,
            json={
                "refresh_token": REFRESH_TOKEN,
                "access_token": ACCESS_TOKEN,
                "type": "bearer",
                "expires_in": 60,
            },
        )

        result = await self.hass.config_entries.flow.async_configure(result["flow_id"])
        assert result.get("type") is FlowResultType.CREATE_ENTRY
        assert result.get("title") == self.title
        assert "data" in result
        assert "token" in result["data"]
        return result