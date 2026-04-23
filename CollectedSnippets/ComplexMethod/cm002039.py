def test_sdpa_can_dispatch_on_flash(self):
        if not self.has_attentions:
            self.skipTest(reason="Model architecture does not support attentions")

        device_type, major, _ = get_device_properties()
        if device_type == "cuda" and major < 8:
            self.skipTest(reason="This test requires an NVIDIA GPU with compute capability >= 8.0")
        elif device_type == "rocm" and major < 9:
            self.skipTest(reason="This test requires an AMD GPU with compute capability >= 9.0")
        elif device_type not in ["cuda", "rocm", "xpu"]:
            self.skipTest(reason="This test requires a Nvidia or AMD GPU or an Intel XPU")

        torch.compiler.reset()

        for model_class in self.all_model_classes:
            if not model_class._supports_sdpa:
                self.skipTest(f"{model_class.__name__} does not support SDPA")

            config, inputs_dict = self.model_tester.prepare_config_and_inputs_for_common()
            inputs_dict = self._prepare_for_class(inputs_dict, model_class)
            if config.model_type in ["llava", "llava_next", "vipllava", "video_llava"]:
                self.skipTest(
                    reason="Llava-like models currently (transformers==4.39.1) requires an attention_mask input"
                )
            if config.model_type == "paligemma":
                self.skipTest(
                    "PaliGemma-like models currently (transformers==4.41.0) requires an attention_mask input"
                )
            if config.model_type in ["idefics", "idefics2", "idefics3"]:
                self.skipTest(reason="Idefics currently (transformers==4.39.1) requires an image_attention_mask input")
            model = model_class(config)

            with tempfile.TemporaryDirectory() as tmpdirname:
                model.save_pretrained(tmpdirname)
                model = model_class.from_pretrained(
                    tmpdirname,
                    dtype=torch.float16,
                    attn_implementation={"decoder": "sdpa", "audio_encoder": None, "text_encoder": None},
                )
                model.to(torch_device)

                inputs_dict.pop("attention_mask", None)
                inputs_dict.pop("decoder_attention_mask", None)

                for name, inp in inputs_dict.items():
                    if isinstance(inp, torch.Tensor) and inp.dtype in [torch.float32, torch.float16]:
                        inputs_dict[name] = inp.to(torch.float16)

                with sdpa_kernel(enable_flash=True, enable_math=False, enable_mem_efficient=False):
                    _ = model(**inputs_dict)