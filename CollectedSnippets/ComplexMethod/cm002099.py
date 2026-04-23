def test_generate_with_and_without_position_ids(self):
        ran_any_model = False
        for model_class in self.all_generative_model_classes:
            config, inputs_dict = self.prepare_config_and_inputs_for_generate()
            model = model_class(config).to(torch_device).eval()
            model_forward_args = inspect.signature(model.forward).parameters

            has_3d_rope_positions = any(
                hasattr(module, "get_rope_index")
                for module in (
                    model,
                    getattr(model, "model", None),
                    getattr(model, "language_model", None),
                    getattr(model, "text_model", None),
                )
            )
            if has_3d_rope_positions:
                continue

            if "position_ids" not in model_forward_args or "input_ids" not in inputs_dict:
                self.skipTest("This model doesn't use `position_ids`")

            if config.is_encoder_decoder:
                self.skipTest("This model doesn't prepare `position_ids` in generate")

            ran_any_model = True
            input_ids = inputs_dict["input_ids"]
            seq_length = input_ids.shape[1]
            # ensure left padding
            if "attention_mask" in inputs_dict and 0 in inputs_dict["attention_mask"][:, -1]:
                inputs_dict["attention_mask"] = inputs_dict["attention_mask"].flip(1)
            else:
                generation_config = copy.deepcopy(model.generation_config)
                model._prepare_special_tokens(generation_config)
                inputs_dict["attention_mask"] = model._prepare_attention_mask_for_generation(
                    input_ids, generation_config, model_kwargs={}
                )

            out_wo_positions = model.generate(**inputs_dict, max_new_tokens=5, use_cache=True, do_sample=False)

            # infer position ids from attn mask and generate again
            attention_mask = inputs_dict["attention_mask"]
            position_ids = attention_mask.long().cumsum(-1) - 1
            position_ids = position_ids.masked_fill(attention_mask == 0, 0)
            position_ids = position_ids[..., -seq_length:].view(-1, seq_length)

            out_w_positions = model.generate(
                **inputs_dict, position_ids=position_ids, max_new_tokens=5, use_cache=True, do_sample=False
            )

            # The two sets of generated sequences must match, if generate can infer position ids correctly
            # and can continue adding new ids to the already passed position ids
            self.assertListEqual(out_wo_positions.tolist(), out_w_positions.tolist())

        if not ran_any_model:
            self.skipTest(
                "All model classes in this test use 3D RoPE positions (`get_rope_index`), for which 2D custom "
                "`position_ids` may be accepted but are expected to produce invalid outputs."
            )