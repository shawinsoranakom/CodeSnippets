def test_keep_in_fp32_modules(self):
        """Test that the flag `_keep_in_fp32_modules` and `_keep_in_fp32_modules_strict`  is correctly respected."""
        config, _ = self.model_tester.prepare_config_and_inputs_for_common()
        for model_class in self.all_model_classes:
            with self.subTest(model_class.__name__):
                model = model_class(copy.deepcopy(config))
                if len(model._keep_in_fp32_modules) == 0 and len(model._keep_in_fp32_modules_strict) == 0:
                    self.skipTest(
                        reason=f"{model_class.__name__} class has no _keep_in_fp32_modules or _keep_in_fp32_modules_strict attribute defined"
                    )

                with tempfile.TemporaryDirectory() as tmpdirname:
                    model.save_pretrained(tmpdirname)

                    model = model_class.from_pretrained(tmpdirname, dtype=torch.float16)
                    self.assertFalse(
                        model._keep_in_fp32_modules & model._keep_in_fp32_modules_strict,
                        "We found a layer in both the `_keep_in_fp32_modules` and `_keep_in_fp32_modules_strict` lists. Please remove it from one of the two lists.",
                    )
                    # When reloading in fp16, keep_in_fp32_modules AND keep_in_fp32_modules_strict should be upcasted
                    all_fp32_modules = model._keep_in_fp32_modules | model._keep_in_fp32_modules_strict
                    for name, param in model.state_dict().items():
                        if any(re.search(rf"(?:^|\.){k}(?:\.|$)", name) for k in all_fp32_modules):
                            self.assertTrue(param.dtype == torch.float32, f"{name} not upcasted to fp32")
                        else:
                            self.assertTrue(param.dtype == torch.float16, f"{name} was upcasted but it should NOT be")

                    # When reloading in bf16, only keep_in_fp32_modules_strict should be upcasted
                    model = model_class.from_pretrained(tmpdirname, dtype=torch.bfloat16)
                    for name, param in model.state_dict().items():
                        if any(re.search(rf"(?:^|\.){k}(?:\.|$)", name) for k in model._keep_in_fp32_modules_strict):
                            self.assertTrue(param.dtype == torch.float32, f"{name} not upcasted to fp32")
                        else:
                            self.assertTrue(param.dtype == torch.bfloat16, f"{name} was upcasted but it should NOT be")