def flash_attn_can_dispatch_composite_models(self, attn_implementation: str):
        """
        Tests if composite models can dispatch on flash attention if the sub-models support it.
        The tests is needed as we handle differently composite models and we cannot check them
        with above tests. If any of the sub-models does not support flash attention, we'll raise an error when dispatching
        that particular sub-model. Otherwise we dispatch safely in all sub-models, where "sub-models" are specific
        backbone models (LM/vision/audio/etc)
        """
        if not self.has_attentions:
            self.skipTest(reason="Model architecture does not support attentions")

        if not is_torch_bf16_available_on_device(torch_device):
            self.skipTest(f"bfloat16 not supported on {torch_device} (on the specific device currently used)")

        dtype = torch.bfloat16

        def _expected_attn_implementations(attention_implementation: str) -> set[str]:
            # Allow kernels fallbacks for flash attention tests.
            requested = attention_implementation
            base = requested.removeprefix("paged|")
            prefix = "paged|" if requested.startswith("paged|") else ""

            expected = {requested}
            if base in FLASH_ATTN_KERNEL_FALLBACK:
                expected.add(f"{prefix}{FLASH_ATTN_KERNEL_FALLBACK[base]}")
            return expected

        expected_attn_implementations = _expected_attn_implementations(attn_implementation)

        for model_class in self.all_model_classes:
            config, inputs_dict = self.model_tester.prepare_config_and_inputs_for_common()
            model = model_class(config)
            if not self._is_composite:
                self.skipTest("This model is not a composite model!")

            with tempfile.TemporaryDirectory() as tmpdirname:
                model.save_pretrained(tmpdirname)
                model = model_class.from_pretrained(tmpdirname, dtype=dtype)

                sub_models_supporting_fa = [
                    module._supports_flash_attn
                    for name, module in model.named_modules()
                    if isinstance(module, PreTrainedModel) and name != ""
                ]
                supports_fa_all_modules = (
                    all(sub_models_supporting_fa) if len(sub_models_supporting_fa) > 0 else model._supports_flash_attn
                )
                if not supports_fa_all_modules:
                    with self.assertRaises(ValueError):
                        model_fa = model_class.from_pretrained(
                            tmpdirname,
                            dtype=dtype,
                            attn_implementation=attn_implementation,
                        )
                else:
                    model_fa = model_class.from_pretrained(
                        tmpdirname, dtype=dtype, attn_implementation=attn_implementation
                    )
                    for key in model_fa.config:
                        if isinstance(getattr(model_fa.config, key), PreTrainedConfig):
                            sub_config = getattr(model_fa.config, key)
                            self.assertIn(sub_config._attn_implementation, expected_attn_implementations)

                    has_fa = False
                    for name, submodule in model_fa.named_modules():
                        class_name = submodule.__class__.__name__
                        if (
                            "Attention" in class_name
                            and getattr(submodule, "config", None)
                            and submodule.config._attn_implementation in expected_attn_implementations
                        ):
                            has_fa = True
                            break
                    if not has_fa:
                        raise ValueError(f"The {attn_implementation} model should have {attn_implementation} layers")