def preprocess(self, text, **kwargs):
        if isinstance(text, str):
            text = [text]

        if self.model.config.model_type == "bark":
            # bark Tokenizer is called with BarkProcessor which uses those kwargs
            # Check if generation_config has semantic_config (BarkGenerationConfig) or use default
            max_length = 256
            if hasattr(self.generation_config, "semantic_config"):
                max_length = getattr(self.generation_config.semantic_config, "max_input_semantic_length", 256)
            new_kwargs = {
                "max_length": max_length,
                "add_special_tokens": False,
                "return_attention_mask": True,
                "return_token_type_ids": False,
            }

            # priority is given to kwargs
            new_kwargs.update(kwargs)
            kwargs = new_kwargs

        preprocessor = self.processor if self.processor is not None else self.tokenizer
        if isinstance(text, Chat):
            output = preprocessor.apply_chat_template(
                text.messages,
                tokenize=True,
                return_dict=True,
                **kwargs,
            )
        else:
            # Add speaker ID if needed and user didn't insert at start of text
            if self.model.config.model_type == "csm":
                text = [f"[0]{t}" if not t.startswith("[") else t for t in text]
                kwargs.setdefault("add_special_tokens", True)
            if self.model.config.model_type == "dia":
                text = [f"[S1] {t}" if not t.startswith("[") else t for t in text]
            output = preprocessor(text, **kwargs, return_tensors="pt")

        return output