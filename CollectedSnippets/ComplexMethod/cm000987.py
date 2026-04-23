async def test_empty_url_skips_navigation(self):
        """State with url='' should skip navigation and still restore cookies/storage."""
        session = make_session("empty-url-sess")
        state = {
            "url": "",
            "cookies": [
                {"name": "c1", "value": "v1", "domain": ".example.com", "path": "/"},
            ],
            "local_storage": {"k": "v"},
        }

        mock_mgr = _make_mock_manager()
        mock_mgr.get_file_info_by_path.return_value = MagicMock(id="f-1")
        mock_mgr.read_file.return_value = json.dumps(state).encode("utf-8")

        captured_cmds: list[tuple] = []

        async def track_run(session_name, *args, **kwargs):
            captured_cmds.append((session_name, args))
            return _run_result(rc=0)

        with patch("backend.copilot.tools.agent_browser._run", side_effect=track_run):
            with patch(_GET_MANAGER, new_callable=AsyncMock, return_value=mock_mgr):
                result = await _restore_browser_state(
                    "empty-url-sess", "user1", session
                )

        assert result is True
        # Should NOT have called "open" — no URL to navigate to
        open_cmds = [c for c in captured_cmds if c[1][:1] == ("open",)]
        assert open_cmds == []
        # But cookies and storage should still be restored
        cookie_cmds = [c for c in captured_cmds if c[1][:2] == ("cookies", "set")]
        storage_cmds = [
            c
            for c in captured_cmds
            if len(c[1]) > 2 and c[1][:2] == ("storage", "local")
        ]
        assert len(cookie_cmds) == 1
        assert len(storage_cmds) == 1