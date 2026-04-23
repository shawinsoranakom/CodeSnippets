def test_flash_attention_2_padding_matches_padding_free_with_position_ids_seq_idx_and_fa_kwargs(self):
        if not self.has_attentions:
            self.skipTest(reason="Model architecture does not support attentions")

        max_new_tokens = 30

        for model_class in self.all_generative_model_classes:
            if not model_class._supports_flash_attn:
                self.skipTest(f"{model_class.__name__} does not support Flash Attention 2")

            config, inputs_dict = self.model_tester.prepare_config_and_inputs_for_common()
            if 0 not in inputs_dict.get("attention_mask", []) or "attention_mask" not in inputs_dict:
                self.skipTest("Model dummy inputs should contain padding in their attention mask")

            dummy_input = inputs_dict[model_class.main_input_name]
            if dummy_input.dtype in [torch.float32, torch.bfloat16]:
                dummy_input = dummy_input.to(torch.float16)

            # make sure that all models have enough positions for generation
            if hasattr(config, "max_position_embeddings"):
                config.max_position_embeddings = max_new_tokens + dummy_input.shape[1] + 1

            model = model_class(config)
            if "position_ids" not in inspect.signature(model.forward).parameters:
                self.skipTest("Model does not support position_ids")

            with tempfile.TemporaryDirectory() as tmpdirname:
                model.save_pretrained(tmpdirname)

                # ensure left padding, to adapt for some models
                if 0 in inputs_dict["attention_mask"][:, -1]:
                    inputs_dict["attention_mask"] = inputs_dict["attention_mask"].flip(1)
                dummy_attention_mask = inputs_dict["attention_mask"]
                inputs_dict["input_ids"][~dummy_attention_mask.bool()] = config.get_text_config().pad_token_id
                # Ensure inputs_dict also has labels in it, as their presence/absence can induce
                # dtype conversions. This also lets us compare losses.
                labels = inputs_dict["input_ids"].clone()
                # Mask padding tokens
                labels[~dummy_attention_mask.bool()] = -100
                # Also need to mask the first non-trivial token to match the padding-free batch.
                first_nonneg_idx = (labels >= 0).int().argmax(dim=1)
                labels[torch.arange(labels.size(0), device=labels.device), first_nonneg_idx] = -100
                inputs_dict["labels"] = labels

                model = (
                    model_class.from_pretrained(
                        tmpdirname,
                        dtype=torch.float16,
                        attn_implementation="flash_attention_2",
                    )
                    .to(torch_device)
                    .eval()
                )

                # flatten
                features = [
                    {"input_ids": i[a.bool()].tolist()}
                    for i, a in zip(inputs_dict["input_ids"], inputs_dict["attention_mask"])
                ]

                # add position_ids + fa_kwargs + seq_idx
                data_collator = DataCollatorWithFlattening(
                    return_tensors="pt", return_seq_idx=True, return_flash_attn_kwargs=True
                )
                batch = data_collator(features)
                batch_accelerator = {k: t.to(torch_device) if torch.is_tensor(t) else t for k, t in batch.items()}

                res_padded = model(**inputs_dict)
                res_padfree = model(**batch_accelerator)

                logits_padded = res_padded.logits[inputs_dict["attention_mask"].bool()]
                logits_padfree = res_padfree.logits[0]

                torch.testing.assert_close(logits_padded.argmax(-1), logits_padfree.argmax(-1), rtol=0, atol=0)
                # acceptable numerical instability
                tol = torch.finfo(torch.float16).eps
                torch.testing.assert_close(logits_padded, logits_padfree, rtol=tol, atol=tol)

                loss_padded = res_padded.loss
                loss_padfree = res_padfree.loss
                torch.testing.assert_close(loss_padded, loss_padfree)