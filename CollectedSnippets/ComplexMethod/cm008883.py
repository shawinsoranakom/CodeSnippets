async def test_structured_output_async(
        self,
        model: BaseChatModel,
        schema_type: Literal["pydantic", "typeddict", "json_schema"],
    ) -> None:
        """Test to verify structured output is generated both on invoke and stream.

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
            properly handles both JSON Schema and Pydantic V2 models.

            `langchain_core` implements a [utility function](https://reference.langchain.com/python/langchain_core/utils/?h=convert_to_op#langchain_core.utils.function_calling.convert_to_openai_tool).
            that will accommodate most formats.

            See [example implementation](https://github.com/langchain-ai/langchain/blob/master/libs/partners/openai/langchain_openai/chat_models/base.py).
            of `with_structured_output`.

        """
        if not self.has_structured_output:
            pytest.skip("Test requires structured output.")

        schema, validation_function = _get_joke_class(schema_type)

        chat = model.with_structured_output(schema, **self.structured_output_kwargs)
        ainvoke_callback = _TestCallbackHandler()

        result = await chat.ainvoke(
            "Tell me a joke about cats.", config={"callbacks": [ainvoke_callback]}
        )
        validation_function(result)

        assert len(ainvoke_callback.options) == 1, (
            "Expected on_chat_model_start to be called once"
        )
        assert isinstance(ainvoke_callback.options[0], dict)
        assert isinstance(
            ainvoke_callback.options[0]["ls_structured_output_format"]["schema"], dict
        )
        assert ainvoke_callback.options[0]["ls_structured_output_format"][
            "schema"
        ] == convert_to_json_schema(schema)

        astream_callback = _TestCallbackHandler()

        chunk = None
        async for chunk in chat.astream(
            "Tell me a joke about cats.", config={"callbacks": [astream_callback]}
        ):
            validation_function(chunk)
        assert chunk is not None, "Stream returned no chunks - possible API issue"

        assert len(astream_callback.options) == 1, (
            "Expected on_chat_model_start to be called once"
        )

        assert isinstance(astream_callback.options[0], dict)
        assert isinstance(
            astream_callback.options[0]["ls_structured_output_format"]["schema"], dict
        )
        assert astream_callback.options[0]["ls_structured_output_format"][
            "schema"
        ] == convert_to_json_schema(schema)