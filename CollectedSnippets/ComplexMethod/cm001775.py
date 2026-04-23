def test_sdpa_can_dispatch_non_composite_models(self):
        """
        Tests if non-composite models dispatch correctly on SDPA/eager when requested so when loading the model.
        This tests only by looking at layer names, as usually SDPA layers are called "SDPAAttention".
        """
        if not self.has_attentions:
            self.skipTest(reason="Model architecture does not support attentions")

        if not self.all_model_classes[0]._supports_sdpa or self._is_composite:
            self.skipTest(f"{self.all_model_classes[0].__name__} does not support SDPA")

        for model_class in self.all_model_classes:
            config, inputs_dict = self.model_tester.prepare_config_and_inputs_for_common()
            model = model_class(config)

            with tempfile.TemporaryDirectory() as tmpdirname:
                model.save_pretrained(tmpdirname)
                model_sdpa = model_class.from_pretrained(tmpdirname)
                model_sdpa = model_sdpa.eval().to(torch_device)

                self.assertTrue(model_sdpa.config._attn_implementation == "sdpa")

                model_eager = model_class.from_pretrained(tmpdirname, attn_implementation="eager")
                model_eager = model_eager.eval().to(torch_device)
                self.assertTrue(model_eager.config._attn_implementation == "eager")

                for name, submodule in model_eager.named_modules():
                    class_name = submodule.__class__.__name__
                    if (
                        class_name.endswith("Attention")
                        and getattr(submodule, "config", None)
                        and submodule.config._attn_implementation == "sdpa"
                    ):
                        raise ValueError(
                            f"The eager model should not have SDPA attention layers but got `{class_name}.config._attn_implementation={submodule.config._attn_implementation}`"
                        )