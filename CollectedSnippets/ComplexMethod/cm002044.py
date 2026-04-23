def flash_attn_inference_equivalence(
        self, attn_implementation: str, padding_side: str, atol: float = 4e-2, rtol: float = 4e-2
    ):
        r"""
        Tests the equivalence between the eager and flash attention implementations.
        This test is only for inference and runs with `dtype=torch.bfloat16`.
        """
        if not self.has_attentions:
            self.skipTest(reason="Model architecture does not support attentions")

        # TODO take a look at this
        # head size needs to be a multiple of 8 but needs more adjustments than our current `_prepare_config_headdim`
        if attn_implementation != "flash_attention_2":
            self.skipTest(
                reason="Model fails for every other FA implementation than FA2 due to dim incompatibilities."
            )

        for model_class in self.all_model_classes:
            if not getattr(model_class, "_supports_flash_attn"):
                self.skipTest(f"{model_class.__name__} does not support Flash Attention")

            config, inputs_dict = self.model_tester.prepare_config_and_inputs_for_common()
            model = model_class(config)

            with tempfile.TemporaryDirectory() as tmpdirname:
                model.save_pretrained(tmpdirname)
                model_fa = model_class.from_pretrained(
                    tmpdirname, dtype=torch.bfloat16, attn_implementation=attn_implementation
                )
                model_fa.to(torch_device)

                model = model_class.from_pretrained(tmpdirname, dtype=torch.bfloat16)
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
                if model.config.is_encoder_decoder:
                    decoder_input_ids = inputs_dict.get("decoder_input_ids", dummy_input)[:1]

                    outputs = model(dummy_input, decoder_input_ids=decoder_input_ids, output_hidden_states=True)
                    outputs_fa = model_fa(dummy_input, decoder_input_ids=decoder_input_ids, output_hidden_states=True)
                else:
                    outputs = model(dummy_input, output_hidden_states=True)
                    outputs_fa = model_fa(dummy_input, output_hidden_states=True)

                logits = outputs.vision_hidden_states[-1]
                logits_fa = outputs_fa.vision_hidden_states[-1]

                assert torch.allclose(logits_fa, logits, atol=atol, rtol=rtol)

                if model.config.is_encoder_decoder:
                    other_inputs = {
                        "decoder_input_ids": decoder_input_ids,
                        "decoder_attention_mask": dummy_attention_mask,
                        "output_hidden_states": True,
                    }
                    if dummy_attention_mask is not None:
                        other_inputs["attention_mask"] = dummy_attention_mask

                    outputs = model(dummy_input, **other_inputs)
                    outputs_fa = model_fa(dummy_input, **other_inputs)
                else:
                    other_inputs = {
                        "output_hidden_states": True,
                    }
                    if dummy_attention_mask is not None:
                        other_inputs["attention_mask"] = dummy_attention_mask

                    outputs = model(dummy_input, **other_inputs)
                    outputs_fa = model_fa(dummy_input, **other_inputs)

                logits = outputs.vision_hidden_states[-1]
                logits_fa = outputs_fa.vision_hidden_states[-1]

                if padding_side == "left":
                    assert torch.allclose(logits_fa[1:], logits[1:], atol=atol, rtol=rtol)

                    # check with inference + dropout
                    model.train()
                    _ = model_fa(dummy_input, **other_inputs)
                else:
                    assert torch.allclose(logits_fa[:-1], logits[:-1], atol=atol, rtol=rtol)