def test_enable_input_require_grads_with_gradient_checkpointing(self):
        if not getattr(self.model_tester, "is_training", False):
            self.skipTest(reason="ModelTester is not configured to run training tests")

        config, inputs_dict = self.model_tester.prepare_config_and_inputs_for_common()
        if hasattr(config, "use_cache"):
            config.use_cache = False

        has_verified_model = False

        for model_class in self.all_model_classes:
            if not getattr(model_class, "supports_gradient_checkpointing", False):
                continue

            model = model_class(copy.deepcopy(config))
            try:
                embeddings_module = model.get_input_embeddings()
            except NotImplementedError:
                continue
            if embeddings_module is None:
                continue

            embedding_param = getattr(embeddings_module, "weight", None)
            if embedding_param is None and isinstance(embeddings_module, (tuple, list)):
                for candidate in embeddings_module:
                    if hasattr(candidate, "weight"):
                        embedding_param = candidate.weight
                        break
            if embedding_param is None or not isinstance(embedding_param, torch.Tensor):
                continue

            inputs = self._prepare_for_class(inputs_dict, model_class, return_labels=True)

            model.to(torch_device)
            model.train()

            set_seed(42)
            outputs = model(**inputs)
            loss_tensor = outputs.loss if getattr(outputs, "loss", None) is not None else outputs[0]
            if isinstance(loss_tensor, (tuple, list)):
                loss_tensor = loss_tensor[0]
            if loss_tensor is None or not isinstance(loss_tensor, torch.Tensor) or not loss_tensor.requires_grad:
                model.zero_grad(set_to_none=True)
                continue
            loss = loss_tensor.sum()
            loss.backward()

            baseline_grad = embedding_param.grad
            if (
                baseline_grad is None
                or baseline_grad.abs().sum().item() == 0
                or not torch.isfinite(baseline_grad).all()
            ):
                model.zero_grad(set_to_none=True)
                continue

            model.zero_grad(set_to_none=True)
            model.gradient_checkpointing_enable()
            model.enable_input_require_grads()

            set_seed(42)
            outputs = model(**inputs)
            loss_tensor = outputs.loss if getattr(outputs, "loss", None) is not None else outputs[0]
            if isinstance(loss_tensor, (tuple, list)):
                loss_tensor = loss_tensor[0]
            if loss_tensor is None or not isinstance(loss_tensor, torch.Tensor) or not loss_tensor.requires_grad:
                model.zero_grad(set_to_none=True)
                continue
            loss = loss_tensor.sum()
            loss.backward()

            grad_after_gc = embedding_param.grad
            self.assertIsNotNone(
                grad_after_gc,
                f"{model_class.__name__} should produce embedding gradients when gradient checkpointing is enabled. "
                "This typically means the model is not exposing its embeddings via `get_input_embeddings()` or "
                "a properly configured `_input_embed_layer` attribute.",
            )
            self.assertTrue(
                torch.isfinite(grad_after_gc).all(),
                f"{model_class.__name__} produced non-finite gradients with gradient checkpointing enabled.",
            )
            self.assertGreater(
                grad_after_gc.abs().sum().item(),
                0,
                f"{model_class.__name__} should keep non-zero embedding gradients with gradient checkpointing enabled.",
            )
            has_verified_model = True

        if not has_verified_model:
            self.skipTest(
                reason="No model with a differentiable loss was available to verify enable_input_require_grads with gradient checkpointing."
            )