async def test_store_success_enqueues_episode(self):
        tool = MemoryStoreTool()
        session = _make_session()

        mock_enqueue = AsyncMock()

        with (
            patch(
                "backend.copilot.tools.graphiti_store.is_enabled_for_user",
                new_callable=AsyncMock,
                return_value=True,
            ),
            patch(
                "backend.copilot.tools.graphiti_store.enqueue_episode",
                mock_enqueue,
            ),
        ):
            result = await tool._execute(
                user_id="user-1",
                session=session,
                name="user_prefers_python",
                content="The user prefers Python over JavaScript.",
                source_description="Direct statement",
            )

        assert isinstance(result, MemoryStoreResponse)
        assert result.memory_name == "user_prefers_python"
        assert "queued for storage" in result.message
        assert result.session_id == "test-session"

        mock_enqueue.assert_awaited_once()
        call_kwargs = mock_enqueue.await_args.kwargs
        assert call_kwargs["name"] == "user_prefers_python"
        assert call_kwargs["source_description"] == "Direct statement"
        assert call_kwargs["is_json"] is True
        envelope = json.loads(call_kwargs["episode_body"])
        assert envelope["content"] == "The user prefers Python over JavaScript."
        assert envelope["memory_kind"] == "fact"