def test_sdpa_can_dispatch_on_flash(self):
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
            if config.model_type == "paligemma":
                self.skipTest(
                    "PaliGemma-like models currently (transformers==4.41.0) requires an attention_mask input"
                )
            if config.model_type in [
                "evolla",
                "modernbert",
                "gemma3",
                "t5gemma",
                "diffllama",
                "dpr",
                "eomt",
                "gpt_bigcode",
                "jamba",
                "kosmos-2",
                "mllama",
                "lighton_ocr",
                "parakeet_encoder",
                "parakeet_ctc",
                "pi0",
                "pixtral",
                "sam",
                "sam_hq",
                "zamba2",
                "sam_vision_model",
                "sam2_vision_model",
                "sam_hq_vision_model",
            ]:
                self.skipTest(
                    reason=f"{config.model_type} currently (transformers==4.52.0) automatically adds an attention_mask input"
                )
            if config.model_type in ["idefics", "idefics2", "idefics3"]:
                self.skipTest(reason="Idefics currently (transformers==4.39.1) requires an image_attention_mask input")
            if config.model_type == "sam":
                self.skipTest(reason="SAM requires an attention_mask input for relative positional embeddings")

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
                model = model_class.from_pretrained(tmpdirname, dtype=torch.float16, attn_implementation="sdpa")
                model.to(torch_device)

                inputs_dict.pop("attention_mask", None)
                inputs_dict.pop("decoder_attention_mask", None)

                for name, inp in inputs_dict.items():
                    if isinstance(inp, torch.Tensor) and inp.dtype in [torch.float32, torch.float16]:
                        inputs_dict[name] = inp.to(torch.float16)

                with sdpa_kernel(enable_flash=True, enable_math=False, enable_mem_efficient=False):
                    _ = model(**inputs_dict)