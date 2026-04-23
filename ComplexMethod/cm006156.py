def test_fallback_models_have_metadata(self):
        """Test that fallback models have complete metadata."""
        from lfx.base.models.groq_constants import GROQ_MODELS_DETAILED

        fallback_names = ["llama-3.1-8b-instant", "llama-3.3-70b-versatile"]

        for model in GROQ_MODELS_DETAILED:
            if model["name"] in fallback_names:
                assert model.get("provider") is not None
                assert model.get("icon") is not None
                # Fallback models should support tool calling
                assert model.get("tool_calling") is True
                # Should not be deprecated or unsupported
                assert model.get("deprecated", False) is False
                assert model.get("not_supported", False) is False
                assert model.get("preview", False) is False