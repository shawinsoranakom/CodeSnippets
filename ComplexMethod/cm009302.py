def test_float_token_usage_normalized_to_int_in_usage_metadata(self) -> None:
        """Test that float token counts are cast to int in usage_metadata."""
        model = _make_model()
        response: dict[str, Any] = {
            "choices": [
                {
                    "message": {"role": "assistant", "content": "Hello!"},
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": 585.0,
                "completion_tokens": 56.0,
                "total_tokens": 641.0,
                "completion_tokens_details": {"reasoning_tokens": 10.0},
                "prompt_tokens_details": {"cached_tokens": 20.0},
            },
            "model": MODEL_NAME,
        }
        result = model._create_chat_result(response)
        msg = result.generations[0].message
        assert isinstance(msg, AIMessage)
        usage = msg.usage_metadata
        assert usage is not None
        assert usage["input_tokens"] == 585
        assert isinstance(usage["input_tokens"], int)
        assert usage["output_tokens"] == 56
        assert isinstance(usage["output_tokens"], int)
        assert usage["total_tokens"] == 641
        assert isinstance(usage["total_tokens"], int)
        assert usage["input_token_details"]["cache_read"] == 20
        assert isinstance(usage["input_token_details"]["cache_read"], int)
        assert usage["output_token_details"]["reasoning"] == 10
        assert isinstance(usage["output_token_details"]["reasoning"], int)