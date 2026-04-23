def test_usage_metadata(self, model: BaseChatModel) -> None:
        """Test to verify that the model returns correct usage metadata.

        This test is optional and should be skipped if the model does not return
        usage metadata (see configuration below).

        !!! warning "Behavior changed in `langchain-tests` 0.3.17"

            Additionally check for the presence of `model_name` in the response
            metadata, which is needed for usage tracking in callback handlers.

        ??? note "Configuration"

            By default, this test is run.

            To disable this feature, set `returns_usage_metadata` to `False` in your
            test class:

            ```python
            class TestMyChatModelIntegration(ChatModelIntegrationTests):
                @property
                def returns_usage_metadata(self) -> bool:
                    return False
            ```

            This test can also check the format of specific kinds of usage metadata
            based on the `supported_usage_metadata_details` property.

            This property should be configured as follows with the types of tokens that
            the model supports tracking:

            ```python
            class TestMyChatModelIntegration(ChatModelIntegrationTests):
                @property
                def supported_usage_metadata_details(self) -> dict:
                    return {
                        "invoke": [
                            "audio_input",
                            "audio_output",
                            "reasoning_output",
                            "cache_read_input",
                            "cache_creation_input",
                        ],
                        "stream": [
                            "audio_input",
                            "audio_output",
                            "reasoning_output",
                            "cache_read_input",
                            "cache_creation_input",
                        ],
                    }
            ```

        ??? question "Troubleshooting"

            If this test fails, first verify that your model returns
            `langchain_core.messages.ai.UsageMetadata` dicts
            attached to the returned `AIMessage` object in `_generate`:

            ```python
            return ChatResult(
                generations=[
                    ChatGeneration(
                        message=AIMessage(
                            content="Output text",
                            usage_metadata={
                                "input_tokens": 350,
                                "output_tokens": 240,
                                "total_tokens": 590,
                                "input_token_details": {
                                    "audio": 10,
                                    "cache_creation": 200,
                                    "cache_read": 100,
                                },
                                "output_token_details": {
                                    "audio": 10,
                                    "reasoning": 200,
                                },
                            },
                        )
                    )
                ]
            )
            ```

            Check also that the response includes a `model_name` key in its
            `usage_metadata`.
        """
        if not self.returns_usage_metadata:
            pytest.skip("Not implemented.")

        result = model.invoke("Hello")
        assert result is not None
        assert isinstance(result, AIMessage)

        assert result.usage_metadata is not None
        assert isinstance(result.usage_metadata["input_tokens"], int)
        assert isinstance(result.usage_metadata["output_tokens"], int)
        assert isinstance(result.usage_metadata["total_tokens"], int)

        # Check model_name is in response_metadata
        # Needed for langchain_core.callbacks.usage
        model_name = result.response_metadata.get("model_name")
        assert isinstance(model_name, str)
        assert model_name, "model_name is empty"

        # `input_tokens` is the total, possibly including other unclassified or
        # system-level tokens.
        if "audio_input" in self.supported_usage_metadata_details["invoke"]:
            # Checks if the specific chat model integration being tested has declared
            # that it supports reporting token counts specifically for `audio_input`
            msg = self.invoke_with_audio_input()  # To be implemented in test subclass
            assert (usage_metadata := msg.usage_metadata) is not None
            assert (
                input_token_details := usage_metadata.get("input_token_details")
            ) is not None
            assert isinstance(input_token_details.get("audio"), int)
            # Asserts that total input tokens are at least the sum of the token counts
            assert usage_metadata.get("input_tokens", 0) >= sum(
                v for v in input_token_details.values() if isinstance(v, int)
            )
        if "audio_output" in self.supported_usage_metadata_details["invoke"]:
            msg = self.invoke_with_audio_output()
            assert (usage_metadata := msg.usage_metadata) is not None
            assert (
                output_token_details := usage_metadata.get("output_token_details")
            ) is not None
            assert isinstance(output_token_details.get("audio"), int)
            # Asserts that total output tokens are at least the sum of the token counts
            assert usage_metadata.get("output_tokens", 0) >= sum(
                v for v in output_token_details.values() if isinstance(v, int)
            )
        if "reasoning_output" in self.supported_usage_metadata_details["invoke"]:
            msg = self.invoke_with_reasoning_output()
            assert (usage_metadata := msg.usage_metadata) is not None
            assert (
                output_token_details := usage_metadata.get("output_token_details")
            ) is not None
            assert isinstance(output_token_details.get("reasoning"), int)
            # Asserts that total output tokens are at least the sum of the token counts
            assert usage_metadata.get("output_tokens", 0) >= sum(
                v for v in output_token_details.values() if isinstance(v, int)
            )
        if "cache_read_input" in self.supported_usage_metadata_details["invoke"]:
            msg = self.invoke_with_cache_read_input()
            usage_metadata = msg.usage_metadata
            assert usage_metadata is not None
            input_token_details = usage_metadata.get("input_token_details")
            assert input_token_details is not None
            cache_read_tokens = input_token_details.get("cache_read")
            assert isinstance(cache_read_tokens, int)
            assert cache_read_tokens >= 0
            # Asserts that total input tokens are at least the sum of the token counts
            total_detailed_tokens = sum(
                v for v in input_token_details.values() if isinstance(v, int) and v >= 0
            )
            input_tokens = usage_metadata.get("input_tokens", 0)
            assert isinstance(input_tokens, int)
            assert input_tokens >= total_detailed_tokens
        if "cache_creation_input" in self.supported_usage_metadata_details["invoke"]:
            msg = self.invoke_with_cache_creation_input()
            usage_metadata = msg.usage_metadata
            assert usage_metadata is not None
            input_token_details = usage_metadata.get("input_token_details")
            assert input_token_details is not None
            cache_creation_tokens = input_token_details.get("cache_creation")
            assert isinstance(cache_creation_tokens, int)
            assert cache_creation_tokens >= 0
            # Asserts that total input tokens are at least the sum of the token counts
            total_detailed_tokens = sum(
                v for v in input_token_details.values() if isinstance(v, int) and v >= 0
            )
            input_tokens = usage_metadata.get("input_tokens", 0)
            assert isinstance(input_tokens, int)
            assert input_tokens >= total_detailed_tokens