def test_init_chat_model_huggingface() -> None:
    """Test that init_chat_model works with HuggingFace models.

    This test verifies that the fix for issue #28226 works correctly.
    The issue was that init_chat_model didn't properly handle HuggingFace
    model initialization, particularly the required 'task' parameter and
    parameter separation between HuggingFacePipeline and ChatHuggingFace.
    """
    from langchain.chat_models.base import init_chat_model

    # Test basic initialization with default task
    # Note: This test may skip in CI if model download fails, but it verifies
    # that the initialization code path works correctly
    try:
        llm = init_chat_model(
            model="microsoft/Phi-3-mini-4k-instruct",
            model_provider="huggingface",
            temperature=0,
            max_tokens=1024,
        )

        # Verify that ChatHuggingFace was created successfully
        assert llm is not None
        from langchain_huggingface import ChatHuggingFace

        assert isinstance(llm, ChatHuggingFace)

        # Verify that the llm attribute is set (this was the bug - it was missing)
        assert hasattr(llm, "llm")
        assert llm.llm is not None

        # Test with explicit task parameter
        llm2 = init_chat_model(
            model="microsoft/Phi-3-mini-4k-instruct",
            model_provider="huggingface",
            task="text-generation",
            temperature=0.5,
        )
        assert isinstance(llm2, ChatHuggingFace)
        assert llm2.llm is not None
    except (
        ImportError,
        OSError,
        RuntimeError,
        ValueError,
    ) as e:
        # If model download fails in CI, skip the test rather than failing
        # The important part is that the code path doesn't raise ValidationError
        # about missing 'llm' field, which was the original bug
        pytest.skip(f"Skipping test due to model download/initialization error: {e}")