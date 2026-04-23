def test_resize_embeddings_untied_no_reinit_on_post_init(self):
        if not self.test_resize_embeddings:
            self.skipTest(reason="test_resize_embeddings is set to `False`")

        original_config, inputs_dict = self.model_tester.prepare_config_and_inputs_for_common()
        original_config.tie_word_embeddings = False
        try:
            original_config.get_text_config().tie_word_embeddings = False
        except Exception as e:
            model_type = getattr(original_config, "model_type", "unknown")
            print(f"Could not set text config's `tie_word_embeddings` for model type `{model_type}`: {e}")

        if original_config.tie_word_embeddings:
            self.skipTest(reason="Model cannot untie embeddings")

        for model_class in self.all_model_classes:
            with self.subTest(model_class):
                config = copy.deepcopy(original_config)
                model = model_class(config).to(torch_device)
                model.eval()

                # The bug only affects nn.Linear LM heads created by _get_resized_lm_head
                output_embeds = model.get_output_embeddings()
                if not isinstance(output_embeds, nn.Linear):
                    continue

                model_vocab_size = config.get_text_config().vocab_size
                try:
                    model.resize_token_embeddings(model_vocab_size + 10)
                except (NotImplementedError, AttributeError):
                    continue

                output_embeds = model.get_output_embeddings()
                weights_before = output_embeds.weight.data.clone()
                bias_before = output_embeds.bias.data.clone() if output_embeds.bias is not None else None

                model.post_init()

                output_embeds_after = model.get_output_embeddings()
                self.assertTrue(
                    torch.equal(weights_before, output_embeds_after.weight.data),
                    "Output embedding weights were reinitialized by post_init() after resize_token_embeddings()",
                )
                if bias_before is not None:
                    self.assertTrue(
                        torch.equal(bias_before, output_embeds_after.bias.data),
                        "Output embedding bias was reinitialized by post_init() after resize_token_embeddings()",
                    )