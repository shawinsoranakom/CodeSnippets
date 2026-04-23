def test_structured_output_pydantic_2_v1(self, model: BaseChatModel) -> None:
        """Test structured output using pydantic.v1.BaseModel.

        Verify we can generate structured output using `pydantic.v1.BaseModel`.

        `pydantic.v1.BaseModel` is available in the Pydantic 2 package.

        This test is optional and should be skipped if the model does not support
        structured output (see configuration below).

        ??? note "Configuration"

            To disable structured output tests, set `has_structured_output` to `False`
            in your test class:

            ```python
            class TestMyChatModelIntegration(ChatModelIntegrationTests):
                @property
                def has_structured_output(self) -> bool:
                    return False
            ```

            By default, `has_structured_output` is `True` if a model overrides the
            `with_structured_output` or `bind_tools` methods.

        ??? question "Troubleshooting"

            If this test fails, ensure that the model's `bind_tools` method
            properly handles both JSON Schema and Pydantic V1 models.

            `langchain_core` implements a [utility function](https://reference.langchain.com/python/langchain_core/utils/?h=convert_to_op#langchain_core.utils.function_calling.convert_to_openai_tool).
            that will accommodate most formats.

            See [example implementation](https://github.com/langchain-ai/langchain/blob/master/libs/partners/openai/langchain_openai/chat_models/base.py).
            of `with_structured_output`.

        """
        if not self.has_structured_output:
            pytest.skip("Test requires structured output.")

        class Joke(BaseModelV1):  # Uses langchain_core.pydantic_v1.BaseModel
            """Joke to tell user."""

            setup: str = FieldV1(description="question to set up a joke")
            punchline: str = FieldV1(description="answer to resolve the joke")

        # Pydantic class
        # Note: with_structured_output return type is dict | pydantic.BaseModel (v2),
        # but this test validates pydantic.v1.BaseModel support at runtime.
        chat = model.with_structured_output(Joke, **self.structured_output_kwargs)
        result = chat.invoke("Tell me a joke about cats.")
        assert isinstance(result, Joke)  # type: ignore[unreachable]

        chunk = None  # type: ignore[unreachable]
        for chunk in chat.stream("Tell me a joke about cats."):
            assert isinstance(chunk, Joke)
        assert chunk is not None, "Stream returned no chunks - possible API issue"

        # Schema
        chat = model.with_structured_output(
            Joke.schema(), **self.structured_output_kwargs
        )
        result = chat.invoke("Tell me a joke about cats.")
        assert isinstance(result, dict)
        assert set(result.keys()) == {"setup", "punchline"}

        chunk = None
        for chunk in chat.stream("Tell me a joke about cats."):
            assert isinstance(chunk, dict)
        assert chunk is not None, "Stream returned no chunks - possible API issue"
        assert set(chunk.keys()) == {"setup", "punchline"}