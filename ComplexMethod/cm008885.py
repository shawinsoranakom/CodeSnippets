def test_json_mode(self, model: BaseChatModel) -> None:
        """Test [structured output]((https://docs.langchain.com/oss/python/langchain/structured-output)) via JSON mode.

        This test is optional and should be skipped if the model does not support
        the JSON mode feature (see configuration below).

        ??? note "Configuration"

            To disable this test, set `supports_json_mode` to `False` in your
            test class:

            ```python
            class TestMyChatModelIntegration(ChatModelIntegrationTests):
                @property
                def supports_json_mode(self) -> bool:
                    return False
            ```

        ??? question "Troubleshooting"

            See example implementation of `with_structured_output` here: https://python.langchain.com/api_reference/_modules/langchain_openai/chat_models/base.html#BaseChatOpenAI.with_structured_output

        """  # noqa: E501
        if not self.supports_json_mode:
            pytest.skip("Test requires json mode support.")

        from pydantic import BaseModel as BaseModelProper  # noqa: PLC0415
        from pydantic import Field as FieldProper  # noqa: PLC0415

        class Joke(BaseModelProper):
            """Joke to tell user."""

            setup: str = FieldProper(description="question to set up a joke")
            punchline: str = FieldProper(description="answer to resolve the joke")

        # Pydantic class
        chat = model.with_structured_output(Joke, method="json_mode")
        msg = (
            "Tell me a joke about cats. Return the result as a JSON with 'setup' and "
            "'punchline' keys. Return nothing other than JSON."
        )
        result = chat.invoke(msg)
        assert isinstance(result, Joke)

        chunk = None
        for chunk in chat.stream(msg):
            assert isinstance(chunk, Joke)
        assert chunk is not None, "Stream returned no chunks - possible API issue"

        # Schema
        chat = model.with_structured_output(
            Joke.model_json_schema(), method="json_mode"
        )
        result = chat.invoke(msg)
        assert isinstance(result, dict)
        assert set(result.keys()) == {"setup", "punchline"}

        chunk = None
        for chunk in chat.stream(msg):
            assert isinstance(chunk, dict)
        assert chunk is not None, "Stream returned no chunks - possible API issue"
        assert set(chunk.keys()) == {"setup", "punchline"}