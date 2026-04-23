async def test_restores_url_cookies_and_storage(self):
        session = make_session("restore-sess")
        state = {
            "url": "https://example.com/page",
            "cookies": [
                {"name": "sid", "value": "abc", "domain": ".example.com", "path": "/"},
                {
                    "name": "token",
                    "value": "xyz",
                    "domain": ".example.com",
                    "path": "/api",
                },
            ],
            "local_storage": {"theme": "dark", "lang": "en"},
        }

        mock_mgr = _make_mock_manager()
        mock_mgr.get_file_info_by_path.return_value = MagicMock(id="file-1")
        mock_mgr.read_file.return_value = json.dumps(state).encode("utf-8")

        captured_cmds: list[tuple] = []

        async def fake_run(session_name, *args, **kwargs):
            captured_cmds.append((session_name, args))
            return _run_result(rc=0)

        with patch("backend.copilot.tools.agent_browser._run", side_effect=fake_run):
            with patch(_GET_MANAGER, new_callable=AsyncMock, return_value=mock_mgr):
                result = await _restore_browser_state("restore-sess", "user1", session)

        assert result is True
        # First call: open URL
        assert captured_cmds[0] == (
            "restore-sess",
            ("open", "https://example.com/page"),
        )
        # Second: wait for load
        assert captured_cmds[1][1] == ("wait", "--load", "load")
        # Then cookies (2 cookies)
        cookie_cmds = [
            c for c in captured_cmds if len(c[1]) > 1 and c[1][0] == "cookies"
        ]
        assert len(cookie_cmds) == 2
        assert cookie_cmds[0][1] == (
            "cookies",
            "set",
            "sid",
            "abc",
            "--domain",
            ".example.com",
            "--path",
            "/",
        )
        assert cookie_cmds[1][1] == (
            "cookies",
            "set",
            "token",
            "xyz",
            "--domain",
            ".example.com",
            "--path",
            "/api",
        )
        # Then localStorage (2 entries)
        storage_cmds = [
            c
            for c in captured_cmds
            if len(c[1]) > 2 and c[1][:2] == ("storage", "local")
        ]
        assert len(storage_cmds) == 2