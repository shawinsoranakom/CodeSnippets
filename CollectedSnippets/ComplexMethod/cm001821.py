def test_quantized_model_conversion_with_exclusion(self):
        from transformers.integrations.metal_quantization import MetalLinear, replace_with_metal_linear

        model_id = "hf-internal-testing/tiny-random-OPTForCausalLM"
        config = AutoConfig.from_pretrained(model_id)
        quantization_config = MetalConfig(bits=4, group_size=64)

        with torch.device("meta"):
            model = OPTForCausalLM(config)

        nb_linears = sum(1 for m in model.modules() if isinstance(m, nn.Linear))
        model = replace_with_metal_linear(
            model, modules_to_not_convert=["out_proj"], quantization_config=quantization_config, pre_quantized=True
        )
        nb_metal = sum(1 for m in model.modules() if isinstance(m, MetalLinear))
        nb_excluded = sum(1 for name, m in model.named_modules() if "out_proj" in name and isinstance(m, nn.Linear))
        self.assertEqual(nb_metal + nb_excluded, nb_linears)