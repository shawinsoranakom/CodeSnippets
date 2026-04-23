async def test_annotate_string_coercion(self, input_val, expected):
        """OpenAI function-call payloads may send annotate as a string."""
        import os
        import tempfile

        from .workspace_files import WorkspaceWriteResponse

        png_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        write_resp = WorkspaceWriteResponse(
            message="ok",
            file_id="file-abc-123",
            name="shot.png",
            path="/workspace/shot.png",
            mime_type="image/png",
            size_bytes=len(png_bytes),
            download_url="workspace://file-abc-123#image/png",
            session_id="test-session-123",
        )

        fd, path = tempfile.mkstemp(suffix=".png")
        os.close(fd)
        with open(path, "wb") as f:
            f.write(png_bytes)

        try:
            with patch("tempfile.mkstemp", return_value=(fd, path)):
                with patch("os.close"):
                    with patch(
                        "backend.copilot.tools.agent_browser._run",
                        new_callable=AsyncMock,
                        return_value=_run_result(rc=0),
                    ) as mock_run:
                        with patch(
                            "backend.copilot.tools.workspace_files.WriteWorkspaceFileTool._execute",
                            new_callable=AsyncMock,
                            return_value=write_resp,
                        ):
                            with patch("os.unlink"):
                                result = await self.tool._execute(
                                    user_id="user1",
                                    session=self.session,
                                    annotate=input_val,
                                )
        finally:
            try:
                os.unlink(path)
            except OSError:
                pass

        assert isinstance(result, BrowserScreenshotResponse)
        # Verify the --annotate flag was passed (or not) to agent-browser
        run_calls = mock_run.call_args_list
        screenshot_call = [c for c in run_calls if "screenshot" in c.args]
        assert len(screenshot_call) == 1
        if expected:
            assert "--annotate" in screenshot_call[0].args
        else:
            assert "--annotate" not in screenshot_call[0].args