def test_concurrent_calls(self):
        handler = TokenUsageCallbackHandler()
        num_threads = 10
        tokens_per_call = 100

        def call_on_llm_end():
            result = _make_llm_result(
                llm_output={
                    "token_usage": {
                        "prompt_tokens": tokens_per_call,
                        "completion_tokens": tokens_per_call,
                    }
                }
            )
            handler.on_llm_end(result)

        threads = [threading.Thread(target=call_on_llm_end) for _ in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        usage = handler.get_usage()
        assert isinstance(usage, Usage)
        assert usage.input_tokens == num_threads * tokens_per_call
        assert usage.output_tokens == num_threads * tokens_per_call
        assert usage.total_tokens == num_threads * tokens_per_call * 2