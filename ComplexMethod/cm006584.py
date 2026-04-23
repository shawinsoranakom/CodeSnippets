async def test_retry_with_increased_timeout(self, mcp_service):
        """Test that retries use increased timeout (80s total per attempt)."""
        project_id = "test-project"

        with patch.object(mcp_service, "_start_project_composer_process") as mock_start:
            # Simulate failure
            mock_start.side_effect = MCPComposerStartupError("Test error", project_id)

            with patch.object(mcp_service, "_kill_zombie_mcp_processes", new=AsyncMock()):
                with patch.object(mcp_service, "_is_port_available", return_value=True):
                    mcp_service._start_locks[project_id] = asyncio.Lock()

                    auth_config = {
                        "auth_type": "oauth",
                        "oauth_host": "localhost",
                        "oauth_port": "2000",
                        "oauth_server_url": "http://localhost:2000",
                        "oauth_client_id": "test",
                        "oauth_client_secret": "test",
                        "oauth_auth_url": "http://test",
                        "oauth_token_url": "http://test",
                    }

                    with contextlib.suppress(Exception):
                        await mcp_service._do_start_project_composer(
                            project_id=project_id,
                            streamable_http_url="http://test",
                            auth_config=auth_config,
                            max_retries=3,
                        )

                    # Verify _start_project_composer_process was called with correct defaults
                    assert mock_start.call_count == 3
                    for call in mock_start.call_args_list:
                        # Check positional arguments (args) and keyword arguments (kwargs)
                        # max_startup_checks is the 6th argument (index 5) or in kwargs
                        # startup_delay is the 7th argument (index 6) or in kwargs
                        if "max_startup_checks" in call.kwargs:
                            assert call.kwargs["max_startup_checks"] == 40
                        else:
                            assert call.args[5] == 40

                        if "startup_delay" in call.kwargs:
                            assert call.kwargs["startup_delay"] == 2.0
                        else:
                            assert call.args[6] == 2.0