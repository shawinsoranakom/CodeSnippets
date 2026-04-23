def test_eager_matches_sdpa_generate(self):
        """Overwritten -- mochi has custom inputs and custom output checks"""

        max_new_tokens = 5

        for model_class in self.all_generative_model_classes:
            if not model_class._supports_sdpa:
                self.skipTest(f"{model_class.__name__} does not support SDPA")

            config, inputs_dict = self.model_tester.prepare_config_and_inputs_for_common()

            dummy_input = inputs_dict[model_class.main_input_name]
            if dummy_input.dtype in [torch.float32, torch.bfloat16]:
                dummy_input = dummy_input.to(torch.float16)

            inputs_dict[model_class.main_input_name] = dummy_input

            # make sure that all models have enough positions for generation
            if hasattr(config, "max_position_embeddings"):
                config.max_position_embeddings = max_new_tokens + dummy_input.shape[1] + 1

            model = model_class(config)

            with tempfile.TemporaryDirectory() as tmpdirname:
                model.save_pretrained(tmpdirname)

                model_sdpa = model_class.from_pretrained(
                    tmpdirname,
                    dtype=torch.float16,
                ).to(torch_device)

                self.assertTrue(model_sdpa.config._attn_implementation == "sdpa")

                model_eager = model_class.from_pretrained(
                    tmpdirname,
                    dtype=torch.float16,
                    attn_implementation="eager",
                ).to(torch_device)

                self.assertTrue(model_eager.config._attn_implementation == "eager")

                for name, submodule in model_eager.named_modules():
                    class_name = submodule.__class__.__name__
                    if "SdpaAttention" in class_name or "SdpaSelfAttention" in class_name:
                        raise ValueError("The eager model should not have SDPA attention layers")

                has_sdpa = False
                for name, submodule in model_sdpa.named_modules():
                    class_name = submodule.__class__.__name__
                    if "SdpaAttention" in class_name or "SdpaSelfAttention" in class_name:
                        has_sdpa = True
                        break
                if not has_sdpa:
                    raise ValueError("The SDPA model should have SDPA attention layers")

                # Just test that a large cache works as expected
                res_eager = model_eager.generate(
                    **inputs_dict,
                    max_new_tokens=max_new_tokens,
                    do_sample=False,
                    depth_decoder_do_sample=False,
                )

                res_sdpa = model_sdpa.generate(
                    **inputs_dict,
                    max_new_tokens=max_new_tokens,
                    do_sample=False,
                    depth_decoder_do_sample=False,
                )

                torch.testing.assert_close(res_eager.sequences, res_sdpa.sequences)
                torch.testing.assert_close(res_eager.audio_sequences, res_sdpa.audio_sequences)