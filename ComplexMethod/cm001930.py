def flash_attn_inference_equivalence(
        self, attn_implementation: str, padding_side: str, atol: float = 4e-2, rtol: float = 4e-2
    ):
        r"""
        Overwritten to enforce decoder behavior as the model is very easily influenced
        by slight changes in the mask. One major reason for the high fluctuations is
        the extra layernom at the end of the model which shifts the logits a lot.
        """
        if not self.has_attentions:
            self.skipTest(reason="Model architecture does not support attentions")

        for model_class in self.all_model_classes:
            config, inputs_dict = self.model_tester.prepare_config_and_inputs_for_common()
            config.is_decoder = True
            model = model_class(config)

            with tempfile.TemporaryDirectory() as tmpdirname:
                model.save_pretrained(tmpdirname)
                model_fa = model_class.from_pretrained(
                    tmpdirname, torch_dtype=torch.bfloat16, attn_implementation=attn_implementation
                )
                model_fa.to(torch_device)

                model = model_class.from_pretrained(tmpdirname, torch_dtype=torch.bfloat16)
                model.to(torch_device)

                dummy_input = inputs_dict[model.main_input_name][:1]
                if dummy_input.dtype in [torch.float32, torch.float16]:
                    dummy_input = dummy_input.to(torch.bfloat16)

                dummy_attention_mask = inputs_dict.get("attention_mask", None)

                if dummy_attention_mask is not None:
                    dummy_attention_mask = dummy_attention_mask[:1]
                    if padding_side == "left":
                        dummy_attention_mask[:, 1:] = 1
                        dummy_attention_mask[:, :1] = 0
                    else:
                        dummy_attention_mask[:, :-1] = 1
                        dummy_attention_mask[:, -1:] = 0

                # no attention mask
                processed_inputs = {
                    model.main_input_name: dummy_input,
                    "output_hidden_states": True,
                }
                if model.config.is_encoder_decoder:
                    processed_inputs["decoder_input_ids"] = inputs_dict.get("decoder_input_ids", dummy_input)[:1]

                prepared_inputs = self._prepare_for_class(processed_inputs, model_class)
                prepared_inputs = {
                    k: v.to(torch_device) if isinstance(v, torch.Tensor) else v for k, v in prepared_inputs.items()
                }

                outputs = model(**prepared_inputs)
                outputs_fa = model_fa(**prepared_inputs)

                logits = (
                    outputs.hidden_states[-1]
                    if not model.config.is_encoder_decoder
                    else outputs.decoder_hidden_states[-1]
                )
                logits_fa = (
                    outputs_fa.hidden_states[-1]
                    if not model.config.is_encoder_decoder
                    else outputs_fa.decoder_hidden_states[-1]
                )

                assert torch.allclose(logits_fa, logits, atol=atol, rtol=rtol)

                # with attention mask
                if dummy_attention_mask is not None:
                    processed_inputs["attention_mask"] = dummy_attention_mask
                    if model.config.is_encoder_decoder:
                        processed_inputs["decoder_attention_mask"] = dummy_attention_mask

                prepared_inputs = self._prepare_for_class(processed_inputs, model_class)
                prepared_inputs = {
                    k: v.to(torch_device) if isinstance(v, torch.Tensor) else v for k, v in prepared_inputs.items()
                }

                outputs = model(**prepared_inputs)
                outputs_fa = model_fa(**prepared_inputs)

                logits = (
                    outputs.hidden_states[-1]
                    if not model.config.is_encoder_decoder
                    else outputs.decoder_hidden_states[-1]
                )
                logits_fa = (
                    outputs_fa.hidden_states[-1]
                    if not model.config.is_encoder_decoder
                    else outputs_fa.decoder_hidden_states[-1]
                )

                if padding_side == "left":
                    assert torch.allclose(logits_fa[1:], logits[1:], atol=atol, rtol=rtol)

                    # check with inference + dropout
                    model.train()
                    _ = model_fa(**prepared_inputs)
                else:
                    assert torch.allclose(logits_fa[:-1], logits[:-1], atol=atol, rtol=rtol)