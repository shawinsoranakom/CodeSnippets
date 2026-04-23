def test_basic_response(self):
        resp = ResponsesResponse(
            model = "test-model",
            output = [
                ResponsesOutputMessage(
                    content = [ResponsesOutputTextContent(text = "Hello!")]
                ),
            ],
            usage = ResponsesUsage(input_tokens = 10, output_tokens = 5, total_tokens = 15),
        )
        d = resp.model_dump()
        assert d["object"] == "response"
        assert d["status"] == "completed"
        assert d["output"][0]["type"] == "message"
        assert d["output"][0]["content"][0]["type"] == "output_text"
        assert d["output"][0]["content"][0]["text"] == "Hello!"
        assert d["usage"]["input_tokens"] == 10
        assert d["usage"]["output_tokens"] == 5
        assert d["usage"]["total_tokens"] == 15
        # Must NOT have prompt_tokens / completion_tokens
        assert "prompt_tokens" not in d["usage"]
        assert "completion_tokens" not in d["usage"]