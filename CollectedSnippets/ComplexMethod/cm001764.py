def test_resize_embeddings_untied(self):
        if not self.test_resize_embeddings:
            self.skipTest(reason="test_resize_embeddings is set to `False`")

        original_config, inputs_dict = self.model_tester.prepare_config_and_inputs_for_common()
        original_config.tie_word_embeddings = False
        try:
            original_config.get_text_config().tie_word_embeddings = False
        except Exception as e:
            model_type = getattr(original_config, "model_type", "unknown")
            # Config may not have a text config
            print(f"Could not set text config's `tie_word_embeddings` for model type `{model_type}`: {e}")
        inputs_dict.pop("labels", None)

        # if model cannot untied embeddings -> leave test
        if original_config.tie_word_embeddings:
            self.skipTest(reason="Model cannot untied embeddings")

        for model_class in self.all_model_classes:
            with self.subTest(model_class):
                config = copy.deepcopy(original_config)
                if is_deepspeed_zero3_enabled():
                    with deepspeed.zero.Init():
                        model = model_class(config)
                else:
                    model = model_class(config).to(torch_device)
                model.eval()

                # if no output embeddings -> leave test
                if model.get_output_embeddings() is None:
                    continue

                # Check that resizing the token embeddings with a larger vocab size increases the model's vocab size
                model_vocab_size = config.get_text_config().vocab_size
                model.resize_token_embeddings(model_vocab_size + 10)
                new_model_vocab_size = model.config.get_text_config().vocab_size
                self.assertEqual(new_model_vocab_size, model_vocab_size + 10)
                output_embeds = model.get_output_embeddings()
                self.assertEqual(output_embeds.weight.shape[0], model_vocab_size + 10)
                # Check bias if present
                if output_embeds.bias is not None:
                    self.assertEqual(output_embeds.bias.shape[0], model_vocab_size + 10)
                # Check that the model can still do a forward pass successfully (every parameter should be resized)
                if not is_deepspeed_zero3_enabled():
                    # A distriputed launcher is needed for the forward pass when deepspeed is enabled
                    model(**self._prepare_for_class(inputs_dict, model_class))

                # Test multivariate resizing.
                model.resize_token_embeddings(model_vocab_size + 10)
                output_embeds = model.get_output_embeddings()
                # Check that added embeddings mean is close to the old embeddings mean
                if is_deepspeed_zero3_enabled():
                    with deepspeed.zero.GatheredParameters(output_embeds.weight, modifier_rank=None):
                        old_embeddings_mean = torch.mean(output_embeds.weight.data[:-10, :], axis=0)
                        new_embeddings_mean = torch.mean(output_embeds.weight.data[-10:, :], axis=0)
                else:
                    old_embeddings_mean = torch.mean(output_embeds.weight.data[:-10, :], axis=0)
                    new_embeddings_mean = torch.mean(output_embeds.weight.data[-10:, :], axis=0)
                torch.testing.assert_close(old_embeddings_mean, new_embeddings_mean, rtol=1e-3, atol=1e-3)
                # check if the old bias mean close to added bias mean.
                if output_embeds.bias is not None:
                    if is_deepspeed_zero3_enabled():
                        with deepspeed.zero.GatheredParameters(output_embeds.bias, modifier_rank=None):
                            old_bias_mean = torch.mean(output_embeds.bias.data[:-10], axis=0)
                            new_bias_mean = torch.mean(output_embeds.bias.data[-10:], axis=0)
                    else:
                        old_bias_mean = torch.mean(output_embeds.bias.data[:-10], axis=0)
                        new_bias_mean = torch.mean(output_embeds.bias.data[-10:], axis=0)

                    torch.testing.assert_close(old_bias_mean, new_bias_mean, rtol=1e-5, atol=1e-5)

                # Check that resizing the token embeddings with a smaller vocab size decreases the model's vocab size
                model.resize_token_embeddings(model_vocab_size - 15)
                new_model_vocab_size = model.config.get_text_config().vocab_size
                self.assertEqual(new_model_vocab_size, model_vocab_size - 15)
                # Check that it actually resizes the embeddings matrix
                output_embeds = model.get_output_embeddings()
                self.assertEqual(output_embeds.weight.shape[0], model_vocab_size - 15)
                # Check bias if present
                if output_embeds.bias is not None:
                    self.assertEqual(output_embeds.bias.shape[0], model_vocab_size - 15)
                # Check that the model can still do a forward pass successfully (every parameter should be resized)
                # Input ids should be clamped to the maximum size of the vocabulary
                inputs_dict["input_ids"].clamp_(max=model_vocab_size - 15 - 1)
                if "decoder_input_ids" in inputs_dict:
                    inputs_dict["decoder_input_ids"].clamp_(max=model_vocab_size - 15 - 1)
                # Check that the model can still do a forward pass successfully (every parameter should be resized)
                if not is_deepspeed_zero3_enabled():
                    # A distriputed launcher is needed for the forward pass when deepspeed is enabled
                    model(**self._prepare_for_class(inputs_dict, model_class))