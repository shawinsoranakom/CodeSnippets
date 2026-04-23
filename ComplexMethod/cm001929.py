def test_enable_input_require_grads_with_gradient_checkpointing(self):
        if not self.model_tester.is_training:
            self.skipTest(reason="ModelTester not in training mode")

        config, inputs_dict = self.model_tester.prepare_config_and_inputs_for_common()
        config.use_cache = False
        config.return_dict = True

        for model_class in self.all_model_classes:
            if not model_class.supports_gradient_checkpointing:
                continue

            model = model_class(config)
            model.to(torch_device)
            model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
            model.enable_input_require_grads()
            model.train()

            for parameter in model.parameters():
                parameter.requires_grad = False

            vision_module = None
            if hasattr(model, "visual"):
                vision_module = model.visual
            elif hasattr(model, "model") and hasattr(model.model, "visual"):
                vision_module = model.model.visual

            if vision_module is None:
                continue

            target_linear = vision_module.blocks[0].attn.qkv
            target_linear.weight.requires_grad = True
            if target_linear.bias is not None:
                target_linear.bias.requires_grad = True

            inputs = self._prepare_for_class(inputs_dict, model_class, return_labels=True)
            outputs = model(**inputs)

            if hasattr(outputs, "loss") and outputs.loss is not None:
                loss = outputs.loss
            else:
                logits = outputs.logits if hasattr(outputs, "logits") else outputs[0]
                loss = logits.sum()

            loss.backward()

            self.assertIsNotNone(
                target_linear.weight.grad,
                f"qkv weights should receive gradients when enable_input_require_grads is used with gradient checkpointing. Model: {model_class.__name__}",
            )
            self.assertGreater(
                target_linear.weight.grad.abs().sum().item(),
                0,
                f"qkv weights should have non-zero gradients when enable_input_require_grads is used with gradient checkpointing. Model: {model_class.__name__}",
            )