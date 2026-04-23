def _fast_generate_wrapper(*args, **kwargs):
        # Check for vLLM-specific arguments
        if "sampling_params" in kwargs:
            raise ValueError(
                "Unsloth: `sampling_params` is only supported when `fast_inference=True` (vLLM). "
                "Since `fast_inference=False`, use HuggingFace generate arguments instead:\n"
                "  model.fast_generate(**tokens.to('cuda'), max_new_tokens=64, temperature=1.0, top_p=0.95)"
            )

        if "lora_request" in kwargs:
            raise ValueError(
                "Unsloth: `lora_request` is only supported when `fast_inference=True` (vLLM). "
                "Since `fast_inference=False`, LoRA weights are already merged into the model."
            )

        # Check if first positional argument is a string or list of strings
        if len(args) > 0:
            first_arg = args[0]
            is_string_input = False

            if isinstance(first_arg, str):
                is_string_input = True
            elif isinstance(first_arg, (list, tuple)) and len(first_arg) > 0:
                if isinstance(first_arg[0], str):
                    is_string_input = True

            if is_string_input:
                raise ValueError(
                    "Unsloth: Passing text strings to `fast_generate` is only supported "
                    "when `fast_inference=True` (vLLM). Since `fast_inference=False`, you must "
                    "tokenize the input first:\n\n"
                    "  messages = tokenizer.apply_chat_template(\n"
                    '      [{"role": "user", "content": "Your prompt here"}],\n'
                    "      tokenize=True, add_generation_prompt=True,\n"
                    '      return_tensors="pt", return_dict=True\n'
                    "  )\n"
                    "  output = model.fast_generate(\n"
                    "      **messages.to('cuda'),\n"
                    "      max_new_tokens=64,\n"
                    "      temperature=1.0,\n"
                    "  )"
                )

        # Call original generate
        return original_generate(*args, **kwargs)