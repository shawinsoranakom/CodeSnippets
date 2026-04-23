def test_sdpa_can_compile_dynamic(self):
        if not self.has_attentions:
            self.skipTest(reason="Model architecture does not support attentions")

        device_type, major, minor = get_device_properties()
        if device_type == "cuda" and major < 8:
            self.skipTest(reason="This test requires an NVIDIA GPU with compute capability >= 8.0")
        elif device_type == "rocm" and major < 9:
            self.skipTest(reason="This test requires an AMD GPU with compute capability >= 9.0")
        elif device_type not in ["cuda", "rocm", "xpu"]:
            self.skipTest(reason="This test requires a Nvidia or AMD GPU, or an Intel XPU")

        torch.compiler.reset()

        for model_class in self.all_model_classes:
            if not model_class._supports_sdpa:
                self.skipTest(f"{model_class.__name__} does not support SDPA")

            config, inputs_dict = self.model_tester.prepare_config_and_inputs_for_common()
            inputs_dict = self._prepare_for_class(inputs_dict, model_class)
            if config.model_type == "dbrx":
                self.skipTest(
                    "DBRX (transformers==4.40) requires a modification to support dynamic shapes with compile."
                )
            if getattr(config, "cache_implementation", None) == "hybrid":
                self.skipTest(
                    "Cannot compile forward without an existing cache with Hybrid, as `torch._dynamo.mark_static_address` "
                    "is a forbidden call."
                )

            model = model_class(config)

            sub_models_supporting_sdpa = [
                module._supports_sdpa
                for name, module in model.named_modules()
                if isinstance(module, PreTrainedModel) and name != ""
            ]
            supports_sdpa_all_modules = (
                all(sub_models_supporting_sdpa) if len(sub_models_supporting_sdpa) > 0 else model._supports_sdpa
            )
            if not supports_sdpa_all_modules:
                self.skipTest(reason="This models' submodels does not support sdpa")

            with tempfile.TemporaryDirectory() as tmpdirname:
                model.save_pretrained(tmpdirname)
                model = model_class.from_pretrained(tmpdirname, dtype=torch.bfloat16, attn_implementation="sdpa")
                model.to(torch_device)

                # For PyTorch 2.1 - 2.3.0 set `dynamic=True`. In the future setting `dynamic=None` and using `torch._dynamo.mark_dynamic()`
                # on input tensors will be required. `mark_dynamic` currently raises inconsistent shape errors.
                model = torch.compile(model, dynamic=True)

                inputs_dict.pop("attention_mask", None)
                inputs_dict.pop("decoder_attention_mask", None)
                for name, inp in inputs_dict.items():
                    if isinstance(inp, torch.Tensor) and inp.dtype in [torch.float32, torch.float16]:
                        inputs_dict[name] = inp.to(torch.bfloat16)

                # use no_grad to save some memory
                with torch.no_grad():
                    _ = model(**inputs_dict)