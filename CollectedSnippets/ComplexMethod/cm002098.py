def attention_mask_padding_matches_padding_free_with_position_ids(
        self, attn_implementation: str, fa_kwargs: bool = False
    ):
        """
        Tests that the given attention implementation can work with packed sequences and infers the mask
        from position ids. This test requires the model to use new attention mask API which handles packing.
        """
        if not self.has_attentions:
            self.skipTest(reason="Model architecture does not support attentions")

        max_new_tokens = 30
        support_flag = {
            "sdpa": "_supports_sdpa",
            "flash_attention_2": "_supports_flash_attn",
            "flash_attention_3": "_supports_flash_attn",
            "flash_attention_4": "_supports_flash_attn",
        }

        for model_class in self.all_generative_model_classes:
            if attn_implementation != "eager" and not getattr(model_class, support_flag[attn_implementation]):
                self.skipTest(f"{model_class.__name__} does not support {attn_implementation}")

            # can't infer if new attn mask API is supported by assume that only model with attention backend support it
            if not model_class._supports_attention_backend:
                self.skipTest(f"{model_class.__name__} does not support new attention mask API")

            if model_class._is_stateful:  # non-transformer models most probably have no packing support
                self.skipTest(f"{model_class.__name__} doesn't support packing!")

            config, inputs_dict = self.model_tester.prepare_config_and_inputs_for_common()
            if config.is_encoder_decoder:
                self.skipTest("Model is an encoder-decoder")

            if "input_ids" not in inputs_dict or inputs_dict["input_ids"].ndim != 2:
                self.skipTest("Model dummy inputs should contain text input ids")

            if 0 not in inputs_dict.get("attention_mask", []) or "attention_mask" not in inputs_dict:
                self.skipTest("Model dummy inputs should contain padding in their attention mask")

            # make sure that all models have enough positions for generation
            dummy_input_ids = inputs_dict["input_ids"]
            if hasattr(config, "max_position_embeddings"):
                config.max_position_embeddings = max_new_tokens + dummy_input_ids.shape[1] + 1

            model = model_class(config)
            if attn_implementation != "eager":
                if not all(
                    getattr(submodel, support_flag[attn_implementation])
                    for submodel in model.modules()
                    if isinstance(submodel, PreTrainedModel)
                ):
                    self.skipTest(f"At least some parts of {model_class.__name__} don't support {attn_implementation}")

            if "position_ids" not in inspect.signature(model.forward).parameters:
                self.skipTest("Model does not support position_ids")

            if (not fa_kwargs) and "position_ids" not in inspect.signature(model.forward).parameters:
                continue  # this model doesn't accept position ids as input

            with tempfile.TemporaryDirectory() as tmpdirname:
                model.save_pretrained(tmpdirname)

                # Drop all keys except for the minimal set. Hard to manipulate with multimodals etc
                inputs_dict = {k: v for k, v in inputs_dict.items() if k in ["input_ids", "attention_mask"]}

                # Ensure left padding, to adapt for some models
                if 0 in inputs_dict["attention_mask"][:, -1]:
                    inputs_dict["attention_mask"] = inputs_dict["attention_mask"].flip(1)
                dummy_attention_mask = inputs_dict["attention_mask"]
                dummy_input_ids[~dummy_attention_mask.bool()] = config.get_text_config().pad_token_id

                # We need to prepare position ids according to the attention mask as we use it to extract embeddings that
                # rely on the correct position - naively increasing sequences do not suffice anymore atp. The solution here
                # calculates an increasing sequences for all 1s and puts 0s else.
                inputs_dict["position_ids"] = ((inputs_dict["attention_mask"] == 1).long().cumsum(dim=1) - 1) * (
                    inputs_dict["attention_mask"] == 1
                ).long()

                model = (
                    model_class.from_pretrained(
                        tmpdirname,
                        dtype=torch.bfloat16,
                        attn_implementation=attn_implementation,
                    )
                    .to(torch_device)
                    .eval()
                )

                if fa_kwargs:
                    # flatten
                    features = [
                        {"input_ids": i[a.bool()].tolist()} for i, a in zip(dummy_input_ids, dummy_attention_mask)
                    ]

                    # add position_ids + fa_kwargs
                    data_collator = DataCollatorWithFlattening(return_tensors="pt", return_flash_attn_kwargs=True)
                    batch = data_collator(features)
                    padfree_inputs_dict = {
                        k: t.to(torch_device) if torch.is_tensor(t) else t for k, t in batch.items()
                    }
                    padfree_inputs_dict.pop("labels", None)  # can lead to silent upcasts on logits
                else:
                    # create packed position_ids
                    position_ids = (
                        torch.cat([torch.arange(length) for length in dummy_attention_mask.sum(1).tolist()])
                        .long()
                        .unsqueeze(0)
                        .to(torch_device)
                    )
                    padfree_inputs_dict = {
                        "input_ids": dummy_input_ids[dummy_attention_mask.bool()].unsqueeze(0),
                        "position_ids": position_ids,
                    }

                # We need to do simple forward without cache in order to trigger packed SDPA/flex/eager attention path
                res_padded = model(**inputs_dict, use_cache=False)
                res_padfree = model(**padfree_inputs_dict, use_cache=False)

                logits_padded = res_padded.logits[dummy_attention_mask.bool()]
                logits_padfree = res_padfree.logits[0]

                # acceptable numerical instability
                tol = torch.finfo(torch.bfloat16).eps
                torch.testing.assert_close(logits_padded, logits_padfree, rtol=tol, atol=tol)