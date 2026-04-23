def check_training_gradient_checkpointing(self, gradient_checkpointing_kwargs=None):
        if not self.model_tester.is_training:
            self.skipTest(reason="ModelTester is not configured to run training tests")
        """
        We skip some parameters when checking for gradient checkpointing:
        - VQ model, as its training is not supported.
        - A few other modules used for image generation.
        """
        skip_patterns = ["vqmodel", "generation_embeddings", "generation_aligner", "generation_head"]

        for model_class in self.all_model_classes:
            with self.subTest(model_class.__name__):
                if (
                    model_class.__name__
                    in [
                        *get_values(MODEL_MAPPING_NAMES),
                        *get_values(MODEL_FOR_BACKBONE_MAPPING_NAMES),
                    ]
                    or not model_class.supports_gradient_checkpointing
                ):
                    # TODO (ydshieh): use `skipTest` once pytest-dev/pytest-subtests/pull/169 is merged
                    # self.skipTest(reason=f"`supports_gradient_checkpointing` is False for {model_class.__name__}.")
                    continue

                config, inputs_dict = self.model_tester.prepare_config_and_inputs_for_common()
                config.use_cache = False
                config.return_dict = True
                model = model_class(config)

                model.to(torch_device)
                model.gradient_checkpointing_enable(gradient_checkpointing_kwargs=gradient_checkpointing_kwargs)
                model.train()

                # unfreeze additional layers
                for p in model.parameters():
                    p.requires_grad_(True)

                optimizer = torch.optim.SGD(model.parameters(), lr=0.01)

                inputs = self._prepare_for_class(inputs_dict, model_class, return_labels=True)
                loss = model(**inputs).loss
                loss.backward()
                optimizer.step()

                if self.test_all_params_have_gradient:
                    for k, v in model.named_parameters():
                        if v.requires_grad and not reduce(lambda t, s: t | (s in k), skip_patterns, False):
                            self.assertTrue(v.grad is not None, f"{k} in {model_class.__name__} has no gradient!")
                        else:
                            pass