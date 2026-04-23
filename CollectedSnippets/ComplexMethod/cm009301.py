def test_missing_optional_metadata_excluded(self) -> None:
        """Test that absent optional fields are not added to response_metadata."""
        model = _make_model()
        response: dict[str, Any] = {
            "choices": [
                {
                    "message": {"role": "assistant", "content": "Hello!"},
                    "finish_reason": "stop",
                }
            ],
        }
        result = model._create_chat_result(response)
        msg = result.generations[0].message
        assert isinstance(msg, AIMessage)
        assert "system_fingerprint" not in msg.response_metadata
        assert "native_finish_reason" not in msg.response_metadata
        assert "model" not in msg.response_metadata
        assert result.llm_output is not None
        assert "id" not in result.llm_output
        assert "created" not in result.llm_output
        assert "object" not in result.llm_output