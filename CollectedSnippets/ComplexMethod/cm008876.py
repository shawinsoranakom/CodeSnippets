async def test_astream_with_model_override(self, model: BaseChatModel) -> None:
        """Test that model name can be overridden at astream time via kwargs.

        Test is skipped if `supports_model_override` is `False`.

        ??? question "Troubleshooting"

            See troubleshooting for `test_invoke_with_model_override`.
        """
        if not self.supports_model_override:
            pytest.skip("Model override not supported.")

        override_model = self.model_override_value
        if not override_model:
            pytest.skip("model_override_value not specified.")

        full: AIMessageChunk | None = None
        async for chunk in model.astream("Hello", model=override_model):
            assert isinstance(chunk, AIMessageChunk)
            full = chunk if full is None else full + chunk

        assert full is not None

        # Verify the overridden model was used
        model_name = full.response_metadata.get("model_name")
        assert model_name is not None, "model_name not found in response_metadata"
        assert override_model in model_name, (
            f"Expected model '{override_model}' but got '{model_name}'"
        )