async def test_passes_default_model_and_tracks_cost(self) -> None:
        block = _make_block()
        fake_resp = _sim_completion(
            content='{"result": "simulated"}',
            usage=_sim_usage(prompt_tokens=1100, completion_tokens=220, cost=0.000189),
        )
        client, create_mock = self._mock_client(fake_resp)

        with (
            patch(
                "backend.executor.simulator.get_openai_client",
                return_value=client,
            ),
            patch(
                "backend.executor.simulator.persist_and_record_usage",
                new=AsyncMock(return_value=1320),
            ) as mock_track,
        ):
            outputs = []
            async for name, data in simulate_block(
                block, {"query": "hello"}, user_id="user-42"
            ):
                outputs.append((name, data))

        assert ("result", "simulated") in outputs

        create_kwargs = create_mock.await_args.kwargs
        assert create_kwargs["model"] == _DEFAULT_SIMULATOR_MODEL
        assert create_kwargs["extra_body"] == {"usage": {"include": True}}

        track_kwargs = mock_track.await_args.kwargs
        assert track_kwargs["provider"] == "open_router"
        assert track_kwargs["model"] == _DEFAULT_SIMULATOR_MODEL
        assert track_kwargs["user_id"] == "user-42"
        assert track_kwargs["prompt_tokens"] == 1100
        assert track_kwargs["completion_tokens"] == 220
        assert track_kwargs["cost_usd"] == pytest.approx(0.000189)
        assert track_kwargs["session"] is None
        assert track_kwargs["log_prefix"] == "[simulator]"