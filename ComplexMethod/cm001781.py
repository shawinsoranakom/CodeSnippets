def flash_attn_from_config(self, attn_implementation: str, test_fwd_in_train: bool = True):
        r"""
        Tests if the model can be loaded with `attn_implementation` from the config and if the
        weights are not randomly initialized.
        """
        if not self.has_attentions:
            self.skipTest(reason="Model architecture does not support attentions")

        for model_class in self.all_generative_model_classes:  # TODO: this test should run on all classes instead
            if not model_class._supports_flash_attn:
                self.skipTest(f"{model_class.__name__} does not support {attn_implementation}")

            config, inputs_dict = self.model_tester.prepare_config_and_inputs_for_common()
            model = model_class(config)  # let's construct it here to see if any submodels can't support flash attn
            if not all(
                submodel._supports_flash_attn for submodel in model.modules() if isinstance(submodel, PreTrainedModel)
            ):
                self.skipTest(reason=f"At least some parts of this model do not support {attn_implementation}")

            # TODO: to change it in the future with other relevant auto classes
            fa_model = model_class._from_config(
                config, attn_implementation=attn_implementation, dtype=torch.bfloat16
            ).to(torch_device)

            # By default, we perform the forward pass in train mode, because it's more sctrict than eval mode. If the
            # forward pass is successful in train mode, it will also be successful in eval mode. But since some models
            # (eg. gemma3) need different inputs in train mode we have the option to test the forward pass in eval mode.
            if test_fwd_in_train:
                fa_model = fa_model.train()
            else:
                fa_model = fa_model.eval()

            dummy_input = inputs_dict[fa_model.main_input_name]
            if dummy_input.dtype in [torch.float32, torch.float16]:
                dummy_input = dummy_input.to(torch.bfloat16)
            dummy_attention_mask = inputs_dict.get("attention_mask", torch.ones_like(dummy_input))

            if fa_model.config.is_encoder_decoder:
                dummy_decoder_input_ids = inputs_dict["decoder_input_ids"]
                dummy_decoder_attention_mask = inputs_dict["decoder_attention_mask"]
                _ = fa_model(
                    dummy_input,
                    attention_mask=dummy_attention_mask,
                    decoder_input_ids=dummy_decoder_input_ids,
                    decoder_attention_mask=dummy_decoder_attention_mask,
                )
            else:
                _ = fa_model(dummy_input, attention_mask=dummy_attention_mask)

            with tempfile.TemporaryDirectory() as tmpdirname:
                fa_model.save_pretrained(tmpdirname)
                model_from_pretrained = model_class.from_pretrained(tmpdirname)
                self.assertTrue(model_from_pretrained.config._attn_implementation != attn_implementation)