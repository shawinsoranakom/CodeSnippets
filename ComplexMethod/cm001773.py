def flash_attn_inference_equivalence(
        self, attn_implementation: str, padding_side: str, atol: float = 4e-2, rtol: float = 4e-2
    ) -> None:
        r"""
        Tests the equivalence between the eager and flash attention implementations.
        This test is only for inference and runs with `dtype=torch.bfloat16`.
        """
        if not self.has_attentions:
            self.skipTest(reason="Model architecture does not support attentions")

        # This flag is used to know if the test was skipped for all `self.all_model_classes` or not
        _has_run_at_least_one_model = False

        for model_class in self.all_model_classes:
            # Custom kernel which needs the mask interface to be properly usable on these models
            if not model_class._supports_attention_backend and not attn_implementation.startswith("flash_attention"):
                continue

            # Set seed for deterministic test - ensures reproducible model initialization and inputs
            set_seed(42)
            config, inputs_dict = self.model_tester.prepare_config_and_inputs_for_common()

            # flash attention variants does not always support arbitrary headim
            config = self._prepare_config_headdim(config, 16)

            # forcing the prefill size to go over sliding window size to check for SWA correctness
            if getattr(config, "sliding_window", None):
                config.sliding_window = 2

            model = model_class(config)
            if not all(
                submodel._supports_flash_attn for submodel in model.modules() if isinstance(submodel, PreTrainedModel)
            ):
                continue

            # Some models only support a sub set of all FA implementations
            valid_fa_implementations = model._compatible_flash_implementations
            if valid_fa_implementations is not None and attn_implementation not in valid_fa_implementations:
                continue

            # If we end up here, at least one model class was not skipped
            _has_run_at_least_one_model = True
            with tempfile.TemporaryDirectory() as tmpdirname:
                # Save the model so we can reload with correct attention
                model.save_pretrained(tmpdirname)

                # Create first inputs without attention mask
                main_input = inputs_dict[model.main_input_name]
                # Only keep first batch sequence
                if isinstance(main_input, torch.Tensor):
                    main_input = main_input[:1]
                    # Fix the dtype
                    if torch.is_floating_point(main_input):
                        main_input = main_input.to(torch.bfloat16)
                first_inputs = {model.main_input_name: main_input, "output_hidden_states": True}
                # Some models have main input name which is different from input_ids, but require input_ids... e.g. BarkFine
                if model.main_input_name != "input_ids" and "input_ids" in inputs_dict:
                    first_inputs["input_ids"] = inputs_dict["input_ids"][:1]
                # If we have some pixel values, use them as well
                if model.main_input_name != "pixel_values" and "pixel_values" in inputs_dict:
                    # NOTE: this fixes qwen2_5_vl/omni because test break w/ pixel values
                    if "image_grid_thw" in inputs_dict:
                        continue
                    first_inputs["pixel_values"] = inputs_dict["pixel_values"][:1].to(torch.bfloat16)
                # Some VLMs require image_sizes alongside pixel_values, e.g. lighton_ocr, llava_onevision
                if "image_sizes" in inputs_dict:
                    first_inputs["image_sizes"] = inputs_dict["image_sizes"][:1]
                if model.config.is_encoder_decoder:
                    decoder_input_ids = inputs_dict.get("decoder_input_ids", first_inputs.get("input_ids"))
                    if decoder_input_ids is not None:
                        first_inputs["decoder_input_ids"] = decoder_input_ids[:1]

                # Create attention mask with padding
                dummy_attention_mask = inputs_dict.get("attention_mask", None)
                if dummy_attention_mask is not None:
                    dummy_attention_mask = dummy_attention_mask[:1]
                    if padding_side == "left":
                        dummy_attention_mask[:, 1:] = 1
                        dummy_attention_mask[:, 0] = 0
                    else:
                        dummy_attention_mask[:, :-1] = 1
                        dummy_attention_mask[:, -1] = 0

                # Create second inputs with attention mask and padding
                second_inputs = copy.deepcopy(first_inputs)
                if dummy_attention_mask is not None:
                    second_inputs["attention_mask"] = dummy_attention_mask
                    if model.config.is_encoder_decoder:
                        second_inputs["decoder_attention_mask"] = dummy_attention_mask

                # Use prepare for class to account for special attributes (e.g. in QnA models)
                first_inputs = self._prepare_for_class(first_inputs, model_class)
                first_inputs = {
                    k: v.to(torch_device) if isinstance(v, torch.Tensor) else v for k, v in first_inputs.items()
                }
                second_inputs = self._prepare_for_class(second_inputs, model_class)
                second_inputs = {
                    k: v.to(torch_device) if isinstance(v, torch.Tensor) else v for k, v in second_inputs.items()
                }

                model = model_class.from_pretrained(
                    tmpdirname, dtype=torch.bfloat16, attn_implementation="eager", device_map=torch_device
                )

                def _get_output_logits(outputs):
                    if "hidden_states" in outputs:
                        return outputs.hidden_states[-1]
                    elif model.config.is_encoder_decoder:
                        return outputs.decoder_hidden_states[-1]
                    elif "logits_per_image" in outputs:
                        return outputs.logits_per_image
                    else:
                        return outputs.logits

                # First run without attention mask
                outputs = model(**first_inputs)
                logits_1_eager = _get_output_logits(outputs)
                # Second run with attention mask and padding
                outputs = model(**second_inputs)
                logits_2_eager = _get_output_logits(outputs)

                # Switch to FA
                del model
                model = model_class.from_pretrained(
                    tmpdirname, dtype=torch.bfloat16, attn_implementation=attn_implementation, device_map=torch_device
                )
                outputs = model(**first_inputs)
                logits_1_fa = _get_output_logits(outputs)
                # Second run with attention mask and padding
                outputs = model(**second_inputs)
                logits_2_fa = _get_output_logits(outputs)

                # Check the results
                torch.testing.assert_close(logits_1_eager, logits_1_fa, atol=atol, rtol=rtol)
                if padding_side == "left":
                    torch.testing.assert_close(logits_2_eager[1:], logits_2_fa[1:], atol=atol, rtol=rtol)
                else:
                    torch.testing.assert_close(logits_2_eager[:-1], logits_2_fa[:-1], atol=atol, rtol=rtol)

        # In this case, the test should appear as skipped, not successful
        if not _has_run_at_least_one_model:
            self.skipTest(
                f"Model architecture does not support {attn_implementation}, or setting its attention dynamically"
            )