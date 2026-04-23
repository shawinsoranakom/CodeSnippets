def _generate_chat_response_inner(
        self,
        messages: list,
        system_prompt: str = "",
        image = None,
        temperature: float = 0.7,
        top_p: float = 0.9,
        top_k: int = 40,
        min_p: float = 0.0,
        max_new_tokens: int = 256,
        repetition_penalty: float = 1.0,
        cancel_event = None,
        _adapter_state = None,
    ) -> Generator[str, None, None]:
        """
        Inner generation logic. Called by both generate_chat_response
        and generate_with_adapter_control.

        _adapter_state is passed to generate_stream/vision so the background
        thread can toggle adapters under the generation lock.
        """
        if not self.active_model_name:
            yield "Error: No active model"
            return

        model_info = self.models[self.active_model_name]
        is_vision = model_info.get("is_vision", False)
        tokenizer = model_info.get("tokenizer") or model_info.get("processor")
        # Unwrap processor → raw tokenizer for VLMs on the text path
        tokenizer = getattr(tokenizer, "tokenizer", tokenizer)
        top_k = self._normalize_top_k(top_k)

        if is_vision and image:
            # Vision model generation (only when an image is actually provided)
            # Check that the stored processor can actually handle images.
            # FastVisionModel may return a raw tokenizer (e.g. GemmaTokenizerFast)
            # instead of a proper ProcessorMixin for some models (e.g. Gemma-3).
            from transformers import ProcessorMixin

            processor = model_info.get("processor")
            has_image_processing = processor is not None and (
                isinstance(processor, ProcessorMixin)
                or hasattr(processor, "image_processor")
            )
            if has_image_processing:
                yield from self._generate_vision_response(
                    messages,
                    system_prompt,
                    image,
                    temperature,
                    top_p,
                    top_k,
                    min_p,
                    max_new_tokens,
                    repetition_penalty,
                    cancel_event = cancel_event,
                )
                return
            else:
                logger.warning(
                    f"Model '{self.active_model_name}' is marked as vision but its processor "
                    f"({type(processor).__name__}) has no image_processor — "
                    f"falling back to text-only generation (image will be ignored)."
                )

        # Text path: Use training pipeline approach
        # Messages are already in ChatML format from eval.py

        # Step 1: Apply get_chat_template if model is in mapper
        try:
            from utils.datasets import (
                MODEL_TO_TEMPLATE_MAPPER,
                get_tokenizer_chat_template,
            )

            model_name_lower = self.active_model_name.lower()

            # Check if model has a registered template
            if model_name_lower in MODEL_TO_TEMPLATE_MAPPER:
                template_name = MODEL_TO_TEMPLATE_MAPPER[model_name_lower]
                logger.info(
                    f"Applying chat template '{template_name}' for {self.active_model_name}"
                )

                # This modifies the tokenizer with the correct template
                tokenizer = get_chat_template(
                    tokenizer,
                    chat_template = template_name,
                )
            else:
                logger.info(
                    f"No registered Unsloth template for {self.active_model_name}, using tokenizer default"
                )
        except Exception as e:
            logger.warning(f"Could not apply get_chat_template: {e}")

        # Step 2: Format with tokenizer.apply_chat_template()
        if system_prompt:
            template_messages = [
                {"role": "system", "content": system_prompt}
            ] + messages
        else:
            template_messages = messages
        try:
            if not (hasattr(tokenizer, "chat_template") and tokenizer.chat_template):
                raise ValueError(
                    f"Model '{self.active_model_name}' has no chat_template set in its "
                    f"tokenizer_config.json. This is usually a problem with the model's "
                    f"HuggingFace repository — it is missing a 'chat_template' key. "
                    f"Please use a model that includes a chat template, or manually set "
                    f"one via tokenizer.chat_template before inference."
                )
            formatted_prompt = tokenizer.apply_chat_template(
                template_messages, tokenize = False, add_generation_prompt = True
            )
            logger.debug(f"Formatted prompt: {formatted_prompt[:200]}...")
        except Exception as e:
            logger.error(f"Error applying chat template: {e}")
            # Fallback to manual formatting
            formatted_prompt = self.format_chat_prompt(messages, system_prompt)

        # Step 3: Generate
        yield from self.generate_stream(
            formatted_prompt,
            temperature,
            top_p,
            top_k,
            min_p,
            max_new_tokens,
            repetition_penalty,
            cancel_event = cancel_event,
            _adapter_state = _adapter_state,
        )