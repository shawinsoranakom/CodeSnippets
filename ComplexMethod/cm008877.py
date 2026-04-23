def test_batch(self, model: BaseChatModel) -> None:
        """Test to verify that `model.batch([messages])` works.

        This should pass for all integrations. Tests the model's ability to process
        multiple prompts in a single batch.

        ??? question "Troubleshooting"

            First, debug
            `langchain_tests.integration_tests.chat_models.ChatModelIntegrationTests.test_invoke`
            because `batch` has a default implementation that calls `invoke` for
            each message in the batch.

            If that test passes but not this one, you should make sure your `batch`
            method does not raise any exceptions, and that it returns a list of valid
            `AIMessage` objects.

        """
        batch_results = model.batch(["Hello", "Hey"])
        assert batch_results is not None
        assert isinstance(batch_results, list)
        assert len(batch_results) == 2
        for result in batch_results:
            assert result is not None
            assert isinstance(result, AIMessage)
            assert isinstance(result.text, str)
            assert len(result.content) > 0