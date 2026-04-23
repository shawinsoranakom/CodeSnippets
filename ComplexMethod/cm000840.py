async def test_openrouter_base_url_uses_open_router_provider(self):
        resp = _build_completion(usage=_usage_with_cost(0.0002))
        persist = AsyncMock(return_value=0)
        with (
            patch(
                "backend.copilot.service.persist_and_record_usage",
                new=persist,
            ),
            patch(
                "backend.copilot.service.config",
                MagicMock(
                    base_url="https://openrouter.ai/api/v1",
                    title_model="anthropic/claude-haiku",
                ),
            ),
        ):
            await _record_title_generation_cost(
                response=resp, user_id="u", session_id="s"
            )
        persist.assert_awaited_once()
        kwargs = persist.await_args.kwargs
        assert kwargs["provider"] == "open_router"
        assert kwargs["model"] == "anthropic/claude-haiku"
        assert kwargs["prompt_tokens"] == 12
        assert kwargs["completion_tokens"] == 3
        assert kwargs["cost_usd"] == pytest.approx(0.0002)
        assert kwargs["log_prefix"] == "[title]"
        assert kwargs["session"] is None