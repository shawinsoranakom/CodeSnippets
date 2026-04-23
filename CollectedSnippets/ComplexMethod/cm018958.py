async def _wrapper(**kwargs):
        """Wrap the fixture to allow passing arguments to the setup method."""
        url = plex_server_url(entry)
        config_entry = kwargs.get("config_entry", entry)
        disable_clients = kwargs.pop("disable_clients", False)
        disable_gdm = kwargs.pop("disable_gdm", True)
        client_type = kwargs.pop("client_type", None)
        session_type = kwargs.pop("session_type", None)

        if client_type == "plexweb":
            session = session_plexweb
        elif session_type == "photo":
            session = session_photo
        elif session_type == "live_tv":
            session = session_live_tv
            requests_mock.get(f"{url}/livetv/sessions/live_tv_1", text=livetv_sessions)
        elif session_type == "transient":
            session = session_transient
        elif session_type == "unknown":
            session = session_unknown
        else:
            session = session_default

        requests_mock.get(f"{url}/status/sessions", text=session)

        if disable_clients:
            requests_mock.get(f"{url}/clients", text=empty_payload)

        with patch(
            "homeassistant.components.plex.GDM",
            return_value=MockGDM(disabled=disable_gdm),
        ):
            config_entry.add_to_hass(hass)
            assert await hass.config_entries.async_setup(config_entry.entry_id)
            await hass.async_block_till_done()
            websocket_connected(mock_websocket)
            await hass.async_block_till_done()

        return hass.data[DOMAIN][SERVERS][entry.unique_id]