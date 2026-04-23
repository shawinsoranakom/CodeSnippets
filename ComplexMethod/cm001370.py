async def test_three_text_completions_in_sequence(
        self, openai_provider, model_name
    ):
        """3 plain text completions — costs accumulate, no state leaks."""
        responses = [
            _make_openai_completion(
                f"Response {i}", prompt_tok=100 + i * 10, completion_tok=50
            )
            for i in range(3)
        ]
        openai_provider._client.chat.completions.create = AsyncMock(
            side_effect=responses
        )

        results = []
        for i in range(3):
            result = await openai_provider.create_chat_completion(
                model_prompt=[ChatMessage.user(f"Message {i}")],
                model_name=model_name,
            )
            results.append(result)

        # Each call should return distinct content
        assert results[0].response.content == "Response 0"
        assert results[1].response.content == "Response 1"
        assert results[2].response.content == "Response 2"

        # Cost should accumulate across all 3 calls
        assert openai_provider._budget.total_cost > 0
        assert openai_provider._budget.usage.prompt_tokens == sum(
            100 + i * 10 for i in range(3)
        )