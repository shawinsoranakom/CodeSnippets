async def test_astream_cost_survives_final_chunk(self) -> None:
        """Test that cost fields are preserved on the final async streaming chunk.

        Same regression coverage as the sync test above, for the _astream path.
        """
        model = _make_model()
        model.client = MagicMock()
        cost_details = {
            "upstream_inference_cost": 7.745e-05,
            "upstream_inference_prompt_cost": 8.95e-06,
            "upstream_inference_completions_cost": 6.85e-05,
        }
        stream_chunks: list[dict[str, Any]] = [
            {
                "choices": [
                    {"delta": {"role": "assistant", "content": "Hi"}, "index": 0}
                ],
            },
            {
                "choices": [
                    {
                        "delta": {},
                        "finish_reason": "stop",
                        "index": 0,
                    }
                ],
                "model": "openai/gpt-4o-mini",
                "id": "gen-cost-astream",
                "usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 5,
                    "total_tokens": 15,
                    "cost": 7.5e-05,
                    "cost_details": cost_details,
                },
            },
        ]
        model.client.chat.send_async = AsyncMock(
            return_value=_MockAsyncStream(stream_chunks)
        )

        chunks = [c async for c in model.astream("Hello")]
        final = [
            c for c in chunks if c.response_metadata.get("finish_reason") == "stop"
        ]
        assert len(final) == 1
        meta = final[0].response_metadata
        assert meta["cost"] == 7.5e-05
        assert meta["cost_details"] == cost_details
        assert meta["finish_reason"] == "stop"