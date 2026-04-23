def test_compute_module_sizes(self):
        r"""
        Test if we compute the right module sizes needed to generate the device map.
        Also test if we get the right values for `total_byte_count` in `caching_allocator_warmup`.
        """
        from transformers.integrations import FP8Linear
        from transformers.integrations.accelerate import compute_module_sizes
        from transformers.modeling_utils import expand_device_map, get_total_byte_count
        from transformers.quantizers import AutoHfQuantizer

        # we need to preprocess the model like that because device_map calculation happens before we load the weights inside the model.
        # For normal wieghts, it's fine but for quantized weights, the tensors dtype might change during loading.
        with torch.device("meta"):
            config = AutoConfig.from_pretrained(self.model_name)
            model = AutoModelForCausalLM.from_config(config, dtype=torch.bfloat16)
            model_size, _ = compute_module_sizes(model, only_modules=False)

            expected_keys = [name for name, _ in model.named_parameters()] + [
                name for name, _ in model.named_buffers()
            ]
            expanded_device_map = expand_device_map({"": torch_device}, expected_keys)
            total_byte_count = list(get_total_byte_count(model, expanded_device_map).values())[0]

            # testing prequantized = False should be enough, the shape should be the same whether it is pre-quantized or not
            hf_quantizer = AutoHfQuantizer.from_config(FineGrainedFP8Config(), pre_quantized=False)
            hf_quantizer.preprocess_model(model=model, config=model.config)
            quantized_model_size, _ = compute_module_sizes(model, hf_quantizer, only_modules=False)

            expected_keys = [name for name, _ in model.named_parameters()] + [
                name for name, _ in model.named_buffers()
            ]
            expanded_device_map = expand_device_map({"": torch_device}, expected_keys)
            quantized_total_byte_count = list(get_total_byte_count(model, expanded_device_map, hf_quantizer).values())[
                0
            ]

        for name, module in model.named_modules():
            if isinstance(module, FP8Linear):
                # from 16 bits to 8 bits
                assert int(model_size[f"{name}.weight"] // 2) == int(quantized_model_size[f"{name}.weight"])

        # check that we get the same value, as we use `compute_module_sizes` in `get_total_byte_count`
        assert total_byte_count == model_size[""]
        assert quantized_total_byte_count == quantized_model_size[""]

        # we should at least have 1.5 times memory reduction in total
        assert model_size[""] > quantized_model_size[""] * 1.5