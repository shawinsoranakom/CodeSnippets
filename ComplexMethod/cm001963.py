def test_flash_attn_2_inference_equivalence_right_padding(self):
        for model_class in self.all_model_classes:
            if not model_class._supports_flash_attn:
                self.skipTest(f"{model_class.__name__} does not support Flash Attention 2")

            config, inputs_dict = self.model_tester.prepare_config_and_inputs_for_common()
            model = model_class(config)

            with tempfile.TemporaryDirectory() as tmpdirname:
                model.save_pretrained(tmpdirname)
                model_fa = model_class.from_pretrained(
                    tmpdirname, dtype=torch.bfloat16, attn_implementation="flash_attention_2"
                )
                model_fa.to(torch_device)

                model = model_class.from_pretrained(tmpdirname, dtype=torch.bfloat16)
                model.to(torch_device)

                # Ignore copy
                dummy_input = inputs_dict[model.main_input_name]
                if dummy_input.dtype in [torch.float32, torch.float16]:
                    dummy_input = dummy_input.to(torch.bfloat16)

                dummy_attention_mask = inputs_dict.get("attention_mask", None)

                if dummy_attention_mask is not None:
                    # Ignore copy
                    dummy_attention_mask[:, :-1] = 1
                    dummy_attention_mask[:, -1:] = 0

                if model.config.is_encoder_decoder:
                    decoder_input_ids = inputs_dict.get("decoder_input_ids", dummy_input)

                    outputs = model(dummy_input, decoder_input_ids=decoder_input_ids, output_hidden_states=True)
                    outputs_fa = model_fa(dummy_input, decoder_input_ids=decoder_input_ids, output_hidden_states=True)
                else:
                    outputs = model(dummy_input, output_hidden_states=True)
                    outputs_fa = model_fa(dummy_input, output_hidden_states=True)

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

                assert torch.allclose(logits_fa, logits, atol=4e-2, rtol=4e-2)
                # Ignore copy
                other_inputs = {
                    "output_hidden_states": True,
                }
                if dummy_attention_mask is not None:
                    other_inputs["attention_mask"] = dummy_attention_mask

                outputs = model(dummy_input, **other_inputs)
                outputs_fa = model_fa(dummy_input, **other_inputs)

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

                assert torch.allclose(logits_fa[:-1], logits[:-1], atol=4e-2, rtol=4e-2)