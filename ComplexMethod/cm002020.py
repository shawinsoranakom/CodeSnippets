def test_sdpa_can_dispatch_composite_models(self):
        for model_class in self.all_model_classes:
            config, inputs_dict = self.model_tester.prepare_config_and_inputs_for_common()
            model = model_class(config)

            with tempfile.TemporaryDirectory() as tmpdirname:
                model.save_pretrained(tmpdirname)

                # Load the model with SDPA
                model_sdpa = model_class.from_pretrained(
                    tmpdirname,
                    attn_implementation="sdpa",
                )
                model_sdpa = model_sdpa.eval().to(torch_device)

                # Load model with eager attention
                model_eager = model_class.from_pretrained(
                    tmpdirname,
                    attn_implementation="eager",
                )
                model_eager = model_eager.eval().to(torch_device)

            self.assertTrue(model_sdpa.config._attn_implementation == "sdpa")
            self.assertTrue(model_eager.config._attn_implementation == "eager")

            if (
                hasattr(model_sdpa, "vision_model")
                and hasattr(model_sdpa, "high_res_vision_model")
                and hasattr(model_sdpa, "language_model")
            ):
                self.assertTrue(model_sdpa.language_model.config._attn_implementation == "sdpa")
                self.assertTrue(model_sdpa.vision_model.config._attn_implementation == "sdpa")
                self.assertTrue(model_sdpa.high_res_vision_model.config._attn_implementation == "sdpa")
                self.assertTrue(model_eager.language_model.config._attn_implementation == "eager")
                self.assertTrue(model_eager.high_res_vision_model.config._attn_implementation == "eager")

            for name, submodule in model_eager.named_modules():
                class_name = submodule.__class__.__name__
                if (
                    any(re.finditer(r"Attention(?!Pool)", class_name))
                    and getattr(submodule, "config", None)
                    and submodule.config._attn_implementation == "sdpa"
                ):
                    self.assertTrue(submodule.config._attn_implementation == "eager")

            for name, submodule in model_sdpa.named_modules():
                class_name = submodule.__class__.__name__
                if (
                    any(re.finditer(r"Attention(?!Pool)", class_name))
                    and getattr(submodule, "config", None)
                    and submodule.config._attn_implementation == "eager"
                ):
                    self.assertTrue(submodule.config._attn_implementation == "sdpa")