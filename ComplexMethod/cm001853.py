def test_input_embeddings_support_forward_hook(self):
        # Make sure that registering hooks on the input embeddings are indeed called
        # in forward. This is necessary for gradient checkpointing in PEFT, see also #41821.
        # For BART with tied embeddings, encoder and decoder have separate embedding modules,
        # so we need to check that hooks on those modules are called during forward.
        config, inputs_dict = self.model_tester.prepare_config_and_inputs()
        for model_class in self.all_model_classes:
            model = model_class(config)
            model.to(torch_device)
            model.eval()

            hooks = []
            base_model = model.model if hasattr(model, "model") else model

            if hasattr(base_model, "encoder") and hasattr(base_model.encoder, "embed_tokens"):
                hook = unittest.mock.MagicMock(return_value=None)
                base_model.encoder.embed_tokens.register_forward_hook(hook)
                hooks.append(hook)
            if hasattr(base_model, "decoder") and hasattr(base_model.decoder, "embed_tokens"):
                hook = unittest.mock.MagicMock(return_value=None)
                base_model.decoder.embed_tokens.register_forward_hook(hook)
                hooks.append(hook)

            inputs = copy.deepcopy(self._prepare_for_class(inputs_dict, model_class))
            model(**inputs)

            total_calls = sum(hook.call_count for hook in hooks)
            self.assertGreater(total_calls, 0, f"Hooks on embeddings were not called for {model_class.__name__}")