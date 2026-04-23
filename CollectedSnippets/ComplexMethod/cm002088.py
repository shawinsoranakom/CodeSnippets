def test_left_padding_compatibility(
        self, unpadded_custom_inputs: dict | None = None, padded_custom_inputs: dict | None = None
    ):
        """
        Tests that adding left-padding yields the same logits as the original input. Exposes arguments for custom
        inputs for overwrites, to prevent full rewrites of the test when all we need is model-specific input handling.

        ! If you overwrite this test, make sure to document why you need to overwrite it !

        NOTE: left-padding results in small numerical differences. This is expected.
        See https://github.com/huggingface/transformers/issues/25420#issuecomment-1775317535

        Args:
            unpadded_custom_inputs (`dict`, *optional*):
                Used in test overwrites. Custom inputs to add/overwrite over the default test inputs.
            padded_custom_inputs (`dict`, *optional*):
                Used in test overwrites. Custom inputs to add/overwrite over the padded test input handcrafted in this
                test. Commonly used e.g. with multimodal cross attention masks.
        """

        # First, filter out models that don't support left padding
        # 1. The model must support padding
        if not self.has_attentions:
            self.skipTest(reason="This model doesn't support padding.")
        # 2. [encoder-decoder] The model must be a decoder-only architecture. Encoder-based architectures can use
        # right-padding in their (encoder) inputs. Encoder-decoder may use left-padding on their decoder inputs
        # [TODO: lift this restriction? technically, we can test padding the decoder inputs.]
        decoder_only_classes = []
        for model_class in self.all_generative_model_classes:
            config, _ = self.prepare_config_and_inputs_for_generate()
            if config.is_encoder_decoder:
                continue
            else:
                decoder_only_classes.append(model_class)
        if len(decoder_only_classes) == 0:
            self.skipTest(reason="No decoder-only architecture available for this model.")
        # 3. [old models] Decoder-only architectures derived from encoder-decoder models could support it in theory,
        # but we haven't added support for it yet. We skip these models for now.
        has_encoder_attributes = any(
            attr_name
            for attr_name in config.to_dict()
            if attr_name.startswith("encoder") and attr_name != "encoder_no_repeat_ngram_size"
        )
        if has_encoder_attributes:
            self.skipTest(
                reason="The decoder-only derived from encoder-decoder models are not expected to support left-padding."
            )

        # Now we can start testing
        unpadded_custom_inputs = unpadded_custom_inputs or {}
        padded_custom_inputs = padded_custom_inputs or {}

        def _prepare_model_kwargs(model_inputs, signature):
            model_kwargs = {"input_ids": model_inputs["input_ids"], "attention_mask": model_inputs["attention_mask"]}
            if "position_ids" in signature:
                position_ids = torch.cumsum(model_inputs["attention_mask"], dim=-1) - 1
                position_ids.masked_fill_(model_inputs["attention_mask"] == 0, 1)
                model_kwargs["position_ids"] = position_ids
            # forward all other inputs, if they are in the signature
            model_kwargs.update({k: v for k, v in model_inputs.items() if k not in model_kwargs and k in signature})
            return model_kwargs

        for model_class in decoder_only_classes:
            config, inputs_dict = self.prepare_config_and_inputs_for_generate()
            model = model_class(config).to(torch_device).eval()
            signature = inspect.signature(model.forward).parameters.keys()

            # No cache to simplify the test (some models need careful init)
            model.generation_config.use_cache = False
            inputs_dict.update(unpadded_custom_inputs)
            # special case: an inexistent `attention_mask` is a full mask
            inputs_dict["attention_mask"] = inputs_dict.get("attention_mask", None)
            if inputs_dict["attention_mask"] is None:
                inputs_dict["attention_mask"] = torch.ones_like(inputs_dict["input_ids"])

            # Get output logits from inputs without padding
            model_kwargs_wo_padding = _prepare_model_kwargs(inputs_dict, signature)
            next_logits_wo_padding = model(**model_kwargs_wo_padding).logits[:, -1, :]

            # Prepare padding on common inputs (pad length 32)
            input_ids = inputs_dict["input_ids"]
            attention_mask = inputs_dict["attention_mask"]
            pad_token_id = getattr(config.get_text_config(decoder=True), "pad_token_id", None) or 0
            pad_size = (input_ids.shape[0], 32, *input_ids.shape[2:])
            padding = torch.ones(pad_size, dtype=input_ids.dtype, device=torch_device) * pad_token_id

            padded_inputs_dict = copy.deepcopy(inputs_dict)
            padded_inputs_dict["input_ids"] = torch.cat((padding, input_ids), dim=1)
            padded_inputs_dict["attention_mask"] = torch.cat(
                (torch.zeros(pad_size[:2], dtype=input_ids.dtype, device=torch_device), attention_mask), dim=1
            )
            if inputs_dict.get("token_type_ids") is not None:
                padded_inputs_dict["token_type_ids"] = torch.cat(
                    (
                        # Assumption: `0` is a good default value for padding token type ids
                        torch.zeros(pad_size[:2], dtype=input_ids.dtype, device=torch_device),
                        inputs_dict["token_type_ids"],
                    ),
                    dim=1,
                )

            if inputs_dict.get("mm_token_type_ids") is not None:
                padded_inputs_dict["mm_token_type_ids"] = torch.cat(
                    (
                        # `0` is a default value of text-modality type ids
                        torch.zeros(pad_size[:2], dtype=input_ids.dtype, device=torch_device),
                        inputs_dict["mm_token_type_ids"],
                    ),
                    dim=1,
                )

            padded_inputs_dict.update(padded_custom_inputs)

            model_kwargs_with_padding = _prepare_model_kwargs(padded_inputs_dict, signature)
            next_logits_with_padding = model(**model_kwargs_with_padding).logits[:, -1, :]

            # They should result in very similar logits
            torch.testing.assert_close(next_logits_wo_padding, next_logits_with_padding, rtol=1e-5, atol=1e-5)