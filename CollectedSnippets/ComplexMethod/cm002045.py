def test_resize_tokens_embeddings(self):
        # resizing tokens_embeddings of a ModuleList
        original_config, inputs_dict = self.model_tester.prepare_config_and_inputs_for_common()
        if not self.test_resize_embeddings:
            self.skipTest(reason="test_resize_embeddings is False")

        for model_class in self.all_model_classes:
            config = copy.deepcopy(original_config)
            model = model_class(config)
            model.to(torch_device)

            if self.model_tester.is_training is False:
                model.eval()

            model_vocab_size = config.vocab_size
            # Retrieve the embeddings and clone theme
            model_embed_list = model.resize_token_embeddings(model_vocab_size)
            cloned_embeddings_list = [model_embed.weight.clone() for model_embed in model_embed_list]

            # Check that resizing the token embeddings with a larger vocab size increases the model's vocab size
            model_embed_list = model.resize_token_embeddings(model_vocab_size + 10)
            self.assertEqual(model.config.vocab_size, model_vocab_size + 10)

            # Check that it actually resizes the embeddings matrix for each codebook
            for model_embed, cloned_embeddings in zip(model_embed_list, cloned_embeddings_list):
                self.assertEqual(model_embed.weight.shape[0], cloned_embeddings.shape[0] + 10)

            # Check that the model can still do a forward pass successfully (every parameter should be resized)
            model(**self._prepare_for_class(inputs_dict, model_class))

            # Check that resizing the token embeddings with a smaller vocab size decreases the model's vocab size
            model_embed_list = model.resize_token_embeddings(model_vocab_size - 15)
            self.assertEqual(model.config.vocab_size, model_vocab_size - 15)
            for model_embed, cloned_embeddings in zip(model_embed_list, cloned_embeddings_list):
                self.assertEqual(model_embed.weight.shape[0], cloned_embeddings.shape[0] - 15)

            # Check that the model can still do a forward pass successfully (every parameter should be resized)
            # Input ids should be clamped to the maximum size of the vocabulary
            inputs_dict["input_ids"].clamp_(max=model_vocab_size - 15 - 1)

            model(**self._prepare_for_class(inputs_dict, model_class))

            # Check that adding and removing tokens has not modified the first part of the embedding matrix.
            # only check for the first embedding matrix
            models_equal = True
            for p1, p2 in zip(cloned_embeddings_list[0], model_embed_list[0].weight):
                if p1.data.ne(p2.data).sum() > 0:
                    models_equal = False

            self.assertTrue(models_equal)