def _test_attention_implementation(self, attn_implementation):
        """
        Compares the output of generate with the eager attention implementation against other implementations.
        NOTE: despite the test logic being the same, different implementations actually need different decorators, hence
        this separate function.
        """
        max_new_tokens = 30
        support_flag = {
            "sdpa": "_supports_sdpa",
            "flash_attention_2": "_supports_flash_attn",
        }

        if (
            is_flash_attention_requested(requested_attention_implementation=attn_implementation)
            and attn_implementation != "flash_attention_2"
        ):
            self.skipTest(reason="Model fails for every other FA implementation than FA2 (no attention interface).")

        for model_class in self.all_generative_model_classes:
            if attn_implementation != "eager" and not getattr(model_class, support_flag[attn_implementation]):
                self.skipTest(f"{model_class.__name__} does not support `attn_implementation={attn_implementation}`")

            config, original_inputs_dict = self.prepare_config_and_inputs_for_generate()
            inputs_dict = {}
            for input_name, input_data in original_inputs_dict.items():
                if (
                    isinstance(input_data, torch.Tensor)
                    and input_data.dtype in [torch.float32, torch.bfloat16]
                    and input_name != "input_values"
                ):
                    inputs_dict[input_name] = input_data.to(torch.float16)
                else:
                    inputs_dict[input_name] = input_data
            main_input = inputs_dict[model_class.main_input_name]

            # FA doesn't accept masking in the middle of the sequence for now. We usually generate right-padded
            # attention masks at test time and, with generate, the mask will be appended with 1s on the right,
            # resulting in a mask with holes (not supported properly by FA).
            if is_flash_attention_requested(requested_attention_implementation=attn_implementation):
                for input_name in ("attention_mask", "decoder_attention_mask", "encoder_attention_mask"):
                    if input_name in inputs_dict:
                        inputs_dict[input_name] = torch.ones_like(inputs_dict[input_name])

            # make sure that all models have enough positions for generation
            if hasattr(config, "max_position_embeddings"):
                config.max_position_embeddings = max_new_tokens + main_input.shape[1] + 1

            model = model_class(config)

            with tempfile.TemporaryDirectory() as tmpdirname:
                model.save_pretrained(tmpdirname)
                del model
                gc.collect()

                generate_kwargs = {
                    "max_new_tokens": max_new_tokens,
                    "do_sample": False,
                    "return_dict_in_generate": True,
                    "output_scores": True,
                    "use_cache": True,
                }

                model_eager = model_class.from_pretrained(
                    tmpdirname,
                    dtype=torch.float16,
                    attn_implementation="eager",
                ).to(torch_device)
                res_eager = model_eager.generate(**inputs_dict, **generate_kwargs)
                del model_eager
                gc.collect()

                model_attn = model_class.from_pretrained(
                    tmpdirname,
                    dtype=torch.float16,
                    attn_implementation=attn_implementation,
                ).to(torch_device)
                res_attn = model_attn.generate(**inputs_dict, **generate_kwargs)
                del model_attn
                gc.collect()

                assert_similar_generate_outputs(res_eager, res_attn, atol=1e-3, rtol=1e-3)