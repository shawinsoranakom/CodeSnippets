def test_resize_tokens_embeddings(self):
        if not self.test_resize_embeddings:
            self.skipTest(reason="test_resize_embeddings is set to `False`")
        (
            original_config,
            inputs_dict,
        ) = self.model_tester.prepare_config_and_inputs_for_common()
        inputs_dict.pop("labels", None)

        for model_class in self.all_model_classes:
            config = copy.deepcopy(original_config)
            if is_deepspeed_zero3_enabled():
                with deepspeed.zero.Init():
                    model = model_class(config)
            else:
                model = model_class(config)
                model.to(torch_device)

            model_embed_pre_resize = model.get_input_embeddings()
            type_model_embed_pre_resize = type(model_embed_pre_resize)

            if self.model_tester.is_training is False:
                model.eval()

            model_vocab_size = config.get_text_config().vocab_size
            # Retrieve the embeddings and clone theme
            model_embed = model.resize_token_embeddings(model_vocab_size)
            cloned_embeddings = model_embed.weight.clone()

            # Check that resizing the token embeddings with a larger vocab size increases the model's vocab size
            model_embed = model.resize_token_embeddings(model_vocab_size + 10)
            new_model_vocab_size = model.config.get_text_config().vocab_size
            self.assertEqual(new_model_vocab_size, model_vocab_size + 10)
            # Check that it actually resizes the embeddings matrix
            self.assertEqual(model_embed.weight.shape[0], cloned_embeddings.shape[0] + 10)
            # Check to make sure the type of embeddings returned post resizing is same as type of input
            type_model_embed_post_resize = type(model_embed)
            self.assertEqual(type_model_embed_pre_resize, type_model_embed_post_resize)
            # Check that added embeddings mean is close to the old embeddings mean
            if is_deepspeed_zero3_enabled():
                with deepspeed.zero.GatheredParameters(model_embed.weight, modifier_rank=None):
                    old_embeddings_mean = torch.mean(model_embed.weight.data[:-10, :], axis=0)
                    new_embeddings_mean = torch.mean(model_embed.weight.data[-10:, :], axis=0)
            else:
                old_embeddings_mean = torch.mean(model_embed.weight.data[:-10, :], axis=0)
                new_embeddings_mean = torch.mean(model_embed.weight.data[-10:, :], axis=0)
            torch.testing.assert_close(old_embeddings_mean, new_embeddings_mean, rtol=1e-3, atol=1e-3)

            # Check that the model can still do a forward pass successfully (every parameter should be resized)
            if not is_deepspeed_zero3_enabled():
                # Input ids should be expanded to the new maximum size of the vocabulary
                inputs_dict["input_ids"][:, -2] = new_model_vocab_size - 1

                # A distriputed launcher is needed for the forward pass when deepspeed is enabled
                model_inputs = self._prepare_for_class(inputs_dict, model_class)
                model(**model_inputs)

            # Check that resizing the token embeddings with a smaller vocab size decreases the model's vocab size
            model_embed = model.resize_token_embeddings(model_vocab_size - 15)
            new_model_vocab_size = model.config.get_text_config().vocab_size
            self.assertEqual(new_model_vocab_size, model_vocab_size - 15)
            # Check that it actually resizes the embeddings matrix
            self.assertEqual(model_embed.weight.shape[0], cloned_embeddings.shape[0] - 15)

            # Check that the model can still do a forward pass successfully (every parameter should be resized)
            # Input ids should be clamped to the maximum size of the vocabulary
            inputs_dict["input_ids"].clamp_(max=model_vocab_size - 15 - 1)

            # make sure that decoder_input_ids are resized as well
            if not is_deepspeed_zero3_enabled():
                # A distriputed launcher is needed for the forward pass when deepspeed is enabled
                if "decoder_input_ids" in inputs_dict:
                    inputs_dict["decoder_input_ids"].clamp_(max=model_vocab_size - 15 - 1)
                model_inputs = self._prepare_for_class(inputs_dict, model_class)
                model(**model_inputs)

            # Check that adding and removing tokens has not modified the first part of the embedding matrix.
            models_equal = True
            for p1, p2 in zip(cloned_embeddings, model_embed.weight):
                if p1.data.ne(p2.data).sum() > 0:
                    models_equal = False

            self.assertTrue(models_equal)

            del model
            del config
            # Copy again. config changed with embedding resizing (`vocab_size` changed)
            config = copy.deepcopy(original_config)
            if is_deepspeed_zero3_enabled():
                with deepspeed.zero.Init():
                    model = model_class(config)
            else:
                model = model_class(config)
                model.to(torch_device)

            model_vocab_size = config.get_text_config().vocab_size
            model.resize_token_embeddings(model_vocab_size + 10, pad_to_multiple_of=1)
            new_model_vocab_size = model.config.get_text_config().vocab_size
            self.assertTrue(new_model_vocab_size + 10, model_vocab_size)

            model_embed = model.resize_token_embeddings(model_vocab_size, pad_to_multiple_of=64)
            new_model_vocab_size = model.config.get_text_config().vocab_size
            self.assertTrue(model_embed.weight.shape[0] // 64, 0)

            self.assertTrue(model_embed.weight.shape[0], new_model_vocab_size)
            self.assertTrue(new_model_vocab_size, model.vocab_size)

            model_embed = model.resize_token_embeddings(model_vocab_size + 13, pad_to_multiple_of=64)
            self.assertTrue(model_embed.weight.shape[0] // 64, 0)

            # Check that resizing a model to a multiple of pad_to_multiple leads to a model of exactly that size
            target_dimension = 128
            model_embed = model.resize_token_embeddings(target_dimension, pad_to_multiple_of=64)
            self.assertTrue(model_embed.weight.shape[0], target_dimension)

            with self.assertRaisesRegex(
                ValueError,
                "Asking to pad the embedding matrix to a multiple of `1.3`, which is not and integer. Please make sure to pass an integer",
            ):
                model.resize_token_embeddings(model_vocab_size, pad_to_multiple_of=1.3)

            # Test when `vocab_size` is smaller than `hidden_size`.
            del model
            del config
            # Copy again. config changed with embedding resizing (`vocab_size` changed)
            config = copy.deepcopy(original_config)
            config.vocab_size = 4
            config.pad_token_id = 3
            if is_deepspeed_zero3_enabled():
                with deepspeed.zero.Init():
                    model = model_class(config)
            else:
                model = model_class(config)
                model.to(torch_device)

            model_vocab_size = config.get_text_config().vocab_size
            # Retrieve the embeddings and clone theme
            model_embed = model.resize_token_embeddings(model_vocab_size)
            cloned_embeddings = model_embed.weight.clone()

            # Check that resizing the token embeddings with a larger vocab size increases the model's vocab size
            model_embed = model.resize_token_embeddings(model_vocab_size + 10)
            new_model_vocab_size = model.config.get_text_config().vocab_size
            self.assertEqual(new_model_vocab_size, model_vocab_size + 10)
            # Check that it actually resizes the embeddings matrix
            self.assertEqual(model_embed.weight.shape[0], cloned_embeddings.shape[0] + 10)
            # Check to make sure the type of embeddings returned post resizing is same as type of input
            type_model_embed_post_resize = type(model_embed)
            self.assertEqual(type_model_embed_pre_resize, type_model_embed_post_resize)
            # Check that added embeddings mean is close to the old embeddings mean
            if is_deepspeed_zero3_enabled():
                with deepspeed.zero.GatheredParameters(model_embed.weight, modifier_rank=None):
                    old_embeddings_mean = torch.mean(model_embed.weight.data[:-10, :], axis=0)
                    new_embeddings_mean = torch.mean(model_embed.weight.data[-10:, :], axis=0)
            else:
                old_embeddings_mean = torch.mean(model_embed.weight.data[:-10, :], axis=0)
                new_embeddings_mean = torch.mean(model_embed.weight.data[-10:, :], axis=0)
            torch.testing.assert_close(old_embeddings_mean, new_embeddings_mean, rtol=1e-3, atol=1e-3)