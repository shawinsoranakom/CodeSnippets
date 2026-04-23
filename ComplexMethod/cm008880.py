def test_usage_metadata_streaming(self, model: BaseChatModel) -> None:
        """Test usage metadata in streaming mode.

        Test to verify that the model returns correct usage metadata in streaming mode.

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

            If this test fails, first verify that your model yields
            `langchain_core.messages.ai.UsageMetadata` dicts
            attached to the returned `AIMessage` object in `_stream`
            that sum up to the total usage metadata.

            Note that `input_tokens` should only be included on one of the chunks
            (typically the first or the last chunk), and the rest should have `0` or
            `None` to avoid counting input tokens multiple times.

            `output_tokens` typically count the number of tokens in each chunk, not
            the sum. This test will pass as long as the sum of `output_tokens` across
            all chunks is not `0`.

            ```python
            yield ChatResult(
                generations=[
                    ChatGeneration(
                        message=AIMessage(
                            content="Output text",
                            usage_metadata={
                                "input_tokens": (
                                    num_input_tokens if is_first_chunk else 0
                                ),
                                "output_tokens": 11,
                                "total_tokens": (
                                    11 + num_input_tokens if is_first_chunk else 11
                                ),
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

            Check also that the aggregated response includes a `model_name` key
            in its `usage_metadata`.

        """
        if not self.returns_usage_metadata:
            pytest.skip("Not implemented.")

        full: AIMessageChunk | None = None
        for chunk in model.stream("Write me 2 haikus. Only include the haikus."):
            assert isinstance(chunk, AIMessageChunk)
            # only one chunk is allowed to set usage_metadata.input_tokens
            # if multiple do, it's likely a bug that will result in overcounting
            # input tokens (since the total number of input tokens applies to the full
            # generation, not individual chunks)
            if full and full.usage_metadata and full.usage_metadata["input_tokens"]:
                assert (
                    not chunk.usage_metadata or not chunk.usage_metadata["input_tokens"]
                ), (
                    "Only one chunk should set input_tokens,"
                    " the rest should be 0 or None"
                )
            # only one chunk is allowed to set usage_metadata.model_name
            # if multiple do, they'll be concatenated incorrectly
            if full and full.usage_metadata and full.usage_metadata.get("model_name"):
                assert not chunk.usage_metadata or not chunk.usage_metadata.get(
                    "model_name"
                ), "Only one chunk should set model_name, the rest should be None"
            full = chunk if full is None else full + chunk

        assert isinstance(full, AIMessageChunk)
        assert full.usage_metadata is not None
        assert isinstance(full.usage_metadata["input_tokens"], int)
        assert isinstance(full.usage_metadata["output_tokens"], int)
        assert isinstance(full.usage_metadata["total_tokens"], int)

        # Check model_name is in response_metadata
        # Needed for langchain_core.callbacks.usage
        model_name = full.response_metadata.get("model_name")
        assert isinstance(model_name, str)
        assert model_name, "model_name is empty"

        if "audio_input" in self.supported_usage_metadata_details["stream"]:
            msg = self.invoke_with_audio_input(stream=True)
            assert msg.usage_metadata is not None
            assert isinstance(
                msg.usage_metadata.get("input_token_details", {}).get("audio"), int
            )
        if "audio_output" in self.supported_usage_metadata_details["stream"]:
            msg = self.invoke_with_audio_output(stream=True)
            assert msg.usage_metadata is not None
            assert isinstance(
                msg.usage_metadata.get("output_token_details", {}).get("audio"), int
            )
        if "reasoning_output" in self.supported_usage_metadata_details["stream"]:
            msg = self.invoke_with_reasoning_output(stream=True)
            assert msg.usage_metadata is not None
            assert isinstance(
                msg.usage_metadata.get("output_token_details", {}).get("reasoning"), int
            )
        if "cache_read_input" in self.supported_usage_metadata_details["stream"]:
            msg = self.invoke_with_cache_read_input(stream=True)
            assert msg.usage_metadata is not None
            assert isinstance(
                msg.usage_metadata.get("input_token_details", {}).get("cache_read"), int
            )
        if "cache_creation_input" in self.supported_usage_metadata_details["stream"]:
            msg = self.invoke_with_cache_creation_input(stream=True)
            assert msg.usage_metadata is not None
            assert isinstance(
                msg.usage_metadata.get("input_token_details", {}).get("cache_creation"),
                int,
            )