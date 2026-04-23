def preprocess(self, inputs=None, timeout=None, continue_final_message=None, **processing_kwargs):
        if isinstance(inputs, Chat):
            # If the user passes a chat that ends in an assistant message, we treat it as a prefill by default
            # because very few models support multiple separate, consecutive assistant messages
            if continue_final_message is None:
                continue_final_message = inputs.messages[-1]["role"] == "assistant"

            # Processor kwargs are passed separately from jinja kwargs to chat template
            # but it was added only in https://github.com/huggingface/transformers/pull/44881
            processor_kwargs = processing_kwargs.pop("processor_kwargs", None) or {}

            chat_template_kwargs = {
                "continue_final_message": continue_final_message,
                "return_tensors": "pt",
                "tokenize": True,
                "return_dict": True,
                "add_generation_prompt": not continue_final_message,
                "processor_kwargs": processor_kwargs,
                **processing_kwargs,
            }

            # Handle Mistral tokenizer which does not accept processing kwargs
            if self.processor.tokenizer.__class__.__name__ == "MistralCommonBackend":
                chat_template_kwargs = {
                    k: v for k, v in chat_template_kwargs.items() if k in ["padding", "truncation", "max_length"]
                }

            model_inputs = self.processor.apply_chat_template(
                inputs.messages,
                **chat_template_kwargs,
            ).to(dtype=self.dtype)
            model_inputs["text"] = inputs
            return model_inputs

        # In case we only have text inputs
        if isinstance(inputs, (list, tuple, str)):
            images = None
            text = inputs
            inputs_text = inputs
        else:
            images = load_images(inputs["images"], timeout=timeout)
            text = inputs["text"]
            inputs_text = inputs["text"]

        # if batched text inputs, we set padding to True unless specified otherwise
        processor_kwargs = processing_kwargs.pop("processor_kwargs", None) or processing_kwargs
        if isinstance(text, (list, tuple)) and len(text) > 1:
            processor_kwargs.setdefault("padding", True)
        model_inputs = self.processor(images=images, text=text, return_tensors="pt", **processor_kwargs).to(
            dtype=self.dtype
        )

        model_inputs["text"] = inputs_text

        return model_inputs