async def test_quick_path_uses_sonar_base(self, monkeypatch):
        fake_resp = _fake_response(
            citations=[
                {
                    "title": "hello",
                    "url": "https://example.com",
                    "content": "greeting",
                }
            ],
            answer="Kimi K2.6 launched 2026-04-20 [1].",
            cost=0.01,
        )
        mock_client = self._mock_client(fake_resp)

        monkeypatch.setattr(
            "backend.copilot.tools.web_search._chat_config",
            type(
                "C",
                (),
                {
                    "api_key": "sk-test",
                    "base_url": "https://openrouter.ai/api/v1",
                },
            )(),
        )

        with (
            patch(
                "backend.copilot.tools.web_search.AsyncOpenAI",
                return_value=mock_client,
            ),
            patch(
                "backend.copilot.tools.web_search.persist_and_record_usage",
                new=AsyncMock(return_value=160),
            ) as mock_track,
        ):
            tool = WebSearchTool()
            result = await tool._execute(
                user_id="u1",
                session=self._session(),
                query="kimi k2.6 launch",
                max_results=5,
                deep=False,
            )

        assert isinstance(result, WebSearchResponse)
        assert result.answer == "Kimi K2.6 launched 2026-04-20 [1]."
        assert len(result.results) == 1
        assert result.results[0].snippet == "greeting"

        create_call = mock_client.chat.completions.create.call_args
        assert create_call.kwargs["model"] == "perplexity/sonar"
        # Sonar searches natively — no server-tool extras.
        assert create_call.kwargs["extra_body"] == {"usage": {"include": True}}

        kwargs = mock_track.await_args.kwargs
        assert kwargs["provider"] == "open_router"
        assert kwargs["model"] == "perplexity/sonar"
        assert kwargs["cost_usd"] == pytest.approx(0.01)