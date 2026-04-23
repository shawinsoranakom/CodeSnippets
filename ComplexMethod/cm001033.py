async def test_returns_middle_out_preview_with_retrieval_instructions(self):
        raw = "A" * 200_000

        mock_workspace = MagicMock()
        mock_workspace.id = "ws-1"
        mock_db = AsyncMock()
        mock_db.get_or_create_workspace = AsyncMock(return_value=mock_workspace)

        mock_manager = AsyncMock()

        with (
            patch("backend.copilot.tools.base.workspace_db", return_value=mock_db),
            patch(
                "backend.copilot.tools.base.WorkspaceManager",
                return_value=mock_manager,
            ),
        ):
            result = await _persist_and_summarize(raw, "user-1", "session-1", "tc-123")

        assert "<tool-output-truncated" in result
        assert "</tool-output-truncated>" in result
        assert "total_chars=200000" in result
        assert 'workspace_path="tool-outputs/tc-123.json"' in result
        assert "read_workspace_file" in result
        # Middle-out sentinel from truncate()
        assert "omitted" in result
        # Total result is much shorter than the raw output
        assert len(result) < len(raw)

        # Verify write_file was called with full content
        mock_manager.write_file.assert_awaited_once()
        call_kwargs = mock_manager.write_file.call_args
        assert call_kwargs.kwargs["content"] == raw.encode("utf-8")
        assert call_kwargs.kwargs["path"] == "tool-outputs/tc-123.json"