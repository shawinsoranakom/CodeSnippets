def test_max_tokens_parameter_correct_for_model(self, openai_provider, model_name):
        """Each model must use the right max_tokens parameter name."""
        messages = [ChatMessage.user("hi")]
        _, kwargs, _ = openai_provider._get_chat_completion_args(
            prompt_messages=messages,
            model=model_name,
            max_output_tokens=1000,
        )

        # model_name is a str enum — use .value for string operations,
        # matching how the production code uses model.startswith()
        model_val = model_name.value
        uses_new_param = (
            model_val.startswith("o1")
            or model_val.startswith("o3")
            or model_val.startswith("o4")
            or model_val.startswith("gpt-5")
            or model_val.startswith("gpt-4.1")
            or model_val.startswith("gpt-4o")
        )

        if uses_new_param:
            assert (
                kwargs.get("max_completion_tokens") == 1000
            ), f"{model_name} should use max_completion_tokens"
            assert "max_tokens" not in kwargs
        else:
            assert (
                kwargs.get("max_tokens") == 1000
            ), f"{model_name} should use max_tokens"
            assert "max_completion_tokens" not in kwargs