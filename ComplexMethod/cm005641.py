def preprocess(
        self,
        prompt_text,
        prefix="",
        handle_long_generation=None,
        add_special_tokens=None,
        truncation=None,
        padding=None,
        max_length=None,
        continue_final_message=None,
        tokenizer_encode_kwargs=None,
        tools=None,
        documents=None,
        **generate_kwargs,
    ):
        # Only set non-None tokenizer kwargs, so as to rely on the tokenizer's defaults
        tokenizer_kwargs = {
            "add_special_tokens": add_special_tokens,
            "truncation": truncation,
            "padding": padding,
            "max_length": max_length,  # NOTE: `max_length` is also a `generate` arg. Use `tokenizer_encode_kwargs` to avoid a name clash
        }
        tokenizer_kwargs = {key: value for key, value in tokenizer_kwargs.items() if value is not None}
        tokenizer_kwargs.update(tokenizer_encode_kwargs or {})

        if isinstance(prompt_text, Chat):
            tokenizer_kwargs.pop("add_special_tokens", None)  # ignore add_special_tokens on chats
            # If the user passes a chat that ends in an assistant message, we treat it as a prefill by default
            # because very few models support multiple separate, consecutive assistant messages
            if continue_final_message is None:
                continue_final_message = prompt_text.messages[-1]["role"] == "assistant"
            inputs = self.tokenizer.apply_chat_template(
                prompt_text.messages,
                add_generation_prompt=not continue_final_message,
                continue_final_message=continue_final_message,
                return_dict=True,
                return_tensors="pt",
                tools=tools,
                documents=documents,
                **tokenizer_kwargs,
            )
        else:
            inputs = self.tokenizer(prefix + prompt_text, return_tensors="pt", **tokenizer_kwargs)

        inputs["prompt_text"] = prompt_text

        if handle_long_generation == "hole":
            cur_len = inputs["input_ids"].shape[-1]
            if "max_new_tokens" in generate_kwargs:
                new_tokens = generate_kwargs["max_new_tokens"]
            else:
                new_tokens = generate_kwargs.get("max_length", self.generation_config.max_length) - cur_len
                if new_tokens < 0:
                    raise ValueError("We cannot infer how many new tokens are expected")
            if cur_len + new_tokens > self.tokenizer.model_max_length:
                keep_length = self.tokenizer.model_max_length - new_tokens
                if keep_length <= 0:
                    raise ValueError(
                        "We cannot use `hole` to handle this generation the number of desired tokens exceeds the"
                        " models max length"
                    )

                inputs["input_ids"] = inputs["input_ids"][:, -keep_length:]
                if "attention_mask" in inputs:
                    inputs["attention_mask"] = inputs["attention_mask"][:, -keep_length:]

        return inputs