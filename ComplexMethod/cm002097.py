def test_flash_attention_2_continue_generate_with_position_ids(self):
        """
        Tests whether flash attention can continue its generation from given position ids.

        NOTE: This serves as regression check as we had instances where flash attention entered the varlen
        path here. It should now always enter the base `flash_fn`.
        """

        max_new_tokens = 2
        for model_class in self.all_generative_model_classes:
            if not model_class._supports_flash_attn:
                self.skipTest(f"{model_class.__name__} does not support Flash Attention.")

            config, inputs_dict = self.model_tester.prepare_config_and_inputs_for_common()
            if config.is_encoder_decoder:
                self.skipTest("Model is an encoder-decoder")

            if not hasattr(config.get_text_config(), "use_cache"):
                self.skipTest(f"{model_class.__name__} doesn't support caching")

            if "input_ids" not in inputs_dict or inputs_dict["input_ids"].ndim != 2:
                self.skipTest("Model dummy inputs should contain text input ids")

            # make sure that all models have enough positions for generation
            dummy_input_ids = inputs_dict["input_ids"]
            if hasattr(config, "max_position_embeddings"):
                config.max_position_embeddings = max_new_tokens + dummy_input_ids.shape[1] + 1

            model = model_class(config)
            if not all(
                getattr(submodel, "_supports_flash_attn")
                for submodel in model.modules()
                if isinstance(submodel, PreTrainedModel)
            ):
                self.skipTest(f"At least some parts of {model_class.__name__} don't support flash attention")

            if "position_ids" not in inspect.signature(model.forward).parameters:
                self.skipTest("Model does not support position_ids")

            with tempfile.TemporaryDirectory() as tmpdirname:
                model.save_pretrained(tmpdirname)
                model = (
                    model_class.from_pretrained(
                        tmpdirname,
                        dtype=torch.bfloat16,
                        attn_implementation="flash_attention_2",
                    )
                    .to(torch_device)
                    .eval()
                )

                # Drop all keys except for `input_ids`. Hard to manipulate with multimodals etc
                dummy_input_ids = inputs_dict["input_ids"]
                dummy_position_ids = torch.arange(dummy_input_ids.shape[1], device=torch_device)
                dummy_position_ids = dummy_position_ids.unsqueeze(0).repeat(dummy_input_ids.shape[0], 1)

                # Store cache for the input prompt
                output = model(dummy_input_ids, position_ids=dummy_position_ids, use_cache=True)
                if "past_key_values" not in output:
                    self.skipTest("This model doesn't return `past_key_values`")

                # create new input_ids and position_ids to continue generation re-using the cache
                new_input_ids = output.logits[:, -1, :].float().argmax(-1)[:, None]
                past_length = dummy_input_ids.shape[1]
                position_ids = torch.arange(past_length, past_length + new_input_ids.shape[1], device=torch_device)
                position_ids = position_ids.unsqueeze(0).repeat(new_input_ids.shape[0], 1)

                output = model(
                    input_ids=new_input_ids,
                    past_key_values=output.past_key_values,
                    position_ids=position_ids,
                    use_cache=True,
                )
                next_token_logits = output.logits[:, -1, :].float()

                generate_kwargs = {
                    "pad_token_id": -1,
                    "eos_token_id": -1,
                    "forced_eos_token_id": None,
                    "use_cache": True,
                    "do_sample": False,
                    "return_dict_in_generate": True,
                    "output_logits": True,
                    "max_new_tokens": max_new_tokens,
                }
                generation_out = model.generate(dummy_input_ids, **generate_kwargs)
                next_token_logits_from_generate = generation_out.logits[-1]

                # acceptable numerical instability
                tol = torch.finfo(torch.bfloat16).eps
                torch.testing.assert_close(next_token_logits_from_generate, next_token_logits, rtol=tol, atol=tol)