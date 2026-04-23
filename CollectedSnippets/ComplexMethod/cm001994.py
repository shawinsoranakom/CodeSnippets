def test_sdpa_can_dispatch_composite_models(self):
        """
        Overwritten as it relies on hardcoded namings atm - checking for our case here specifically
        """
        for model_class in self.all_model_classes:
            config, _ = self.model_tester.prepare_config_and_inputs_for_common()
            model = model_class(config)

            with tempfile.TemporaryDirectory() as tmpdirname:
                model.save_pretrained(tmpdirname)
                model = model_class.from_pretrained(tmpdirname)

                sub_models_supporting_sdpa = [
                    (module._supports_sdpa or module._supports_attention_backend)
                    for name, module in model.named_modules()
                    if isinstance(module, PreTrainedModel) and name != ""
                ]
                supports_sdpa_all_modules = (
                    all(sub_models_supporting_sdpa)
                    if len(sub_models_supporting_sdpa) > 0
                    else (model._supports_sdpa or model._supports_attention_backend)
                )

                if not supports_sdpa_all_modules:
                    with self.assertRaises(ValueError):
                        model_sdpa = model_class.from_pretrained(tmpdirname, attn_implementation="sdpa")
                else:
                    model_sdpa = model_class.from_pretrained(tmpdirname, attn_implementation="sdpa")
                    for key in model_sdpa.config:
                        if isinstance(getattr(model_sdpa.config, key), PreTrainedConfig):
                            sub_config = getattr(model_sdpa.config, key)
                            self.assertTrue(sub_config._attn_implementation == "sdpa")