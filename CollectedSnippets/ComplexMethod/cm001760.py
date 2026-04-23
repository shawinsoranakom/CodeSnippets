def check_training_gradient_checkpointing(self, gradient_checkpointing_kwargs=None):
        if not self.model_tester.is_training:
            self.skipTest(reason="ModelTester is not configured to run training tests")

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

                # make sure that test runs are consistent by disabling dropout
                #
                # Note: attention_probs_dropout_prob seem to influence classifier.bias in BertForMultipleChoice
                # (and other Bert derived models). Sometimes classifier.bias is None when
                # attention_probs_dropout_prob > 0. This might indicate a bug somewhere.
                if hasattr(config, "hidden_dropout_prob"):
                    config.hidden_dropout_prob = 0.0
                if hasattr(config, "attention_probs_dropout_prob"):
                    config.attention_probs_dropout_prob = 0.0

                inputs = self._prepare_for_class(inputs_dict, model_class, return_labels=True)

                set_seed(42)
                model = model_class(config)
                model.to(torch_device)
                model.train()

                # unfreeze additional layers
                for p in model.parameters():
                    p.requires_grad_(True)

                # do a non-checkpointing run, so we can compare the set of non-zero gradients later. we skip None
                # grads here to collect a reference set of modules that have non-zero gradients (to filter layers like
                # MoE that drop out parts of the model).
                optimizer = torch.optim.SGD(model.parameters(), lr=0.01)
                set_seed(42)
                loss = model(**inputs).loss
                loss.backward()
                grad_expected_params = [(n, p) for n, p in model.named_parameters() if p.grad is not None]
                non_zero_grads_normal = {n for n, p in grad_expected_params if p.grad.abs().sum() > 0}

                # reset all gradients to zero for the comparison with the gradient checkpointing run
                optimizer.zero_grad()

                # now enable gradient checkpointing and compare the gradients
                model.gradient_checkpointing_enable(gradient_checkpointing_kwargs=gradient_checkpointing_kwargs)

                checkpointing_layer = next(m for m in model.modules() if isinstance(m, GradientCheckpointingLayer))

                optimizer = torch.optim.SGD(model.parameters(), lr=0.01)
                with unittest.mock.patch.object(
                    checkpointing_layer, "forward", wraps=checkpointing_layer.forward
                ) as forward_mock:
                    set_seed(42)
                    loss = model(**inputs).loss
                    loss.backward()
                    optimizer.step()

                    # test that gradient checkpointing is active as it would call the gradient checkpointing layer's
                    # forward more than once.
                    self.assertGreater(forward_mock.call_count, 1)

                # check that all the parameters that had non-zero gradients before, have non-zero grads with gradient
                # checkpointing. divergence indicates a different forward-pass environment that needs special handling.
                non_zero_grads_gradcp = {n for n, p in grad_expected_params if p.grad.abs().sum() > 0}
                self.assertEqual(non_zero_grads_gradcp, non_zero_grads_normal)

                if self.test_all_params_have_gradient:
                    for k, v in model.named_parameters():
                        if v.requires_grad and v.grad is None:
                            if "expert" in k:
                                print(
                                    f"None for {k}, Probaby running a MOE, make sure grad is not NONE on EVERY layer. At LEAST 1 of the expert layer should have grads!"
                                )
                            else:
                                with self.subTest(f"{k}"):
                                    self.assertTrue(
                                        v.grad is not None, f"{k} in {model_class.__name__} has no gradient!"
                                    )