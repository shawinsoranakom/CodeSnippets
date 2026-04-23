def test_quantized_model_conversion(self):
        """
        Simple test that checks if the quantized model has been converted properly
        """
        from vptq import VQuantLinear

        from transformers.integrations import replace_with_vptq_linear

        model_id = "facebook/opt-350m"
        config = AutoConfig.from_pretrained(model_id, revision="cb32f77e905cccbca1d970436fb0f5e6b58ee3c5")
        modules_to_not_convert = ["lm_head"]
        names = [
            "q_proj",
            "k_proj",
            "v_proj",
            "out_proj",
            "fc1",
            "fc2",
        ]
        value = {
            "enable_norm": True,
            "enable_perm": True,
            "group_num": 1,
            "group_size": 128,
            "indices_as_float": False,
            "num_centroids": [-1, 128],
            "num_res_centroids": [-1, 128],
            "outlier_size": 0,
            "vector_lens": [-1, 12],
        }
        shared_layer_config = {}
        for name in names:
            shared_layer_config[name] = value
        for i in range(24):
            modules_to_not_convert.append(f"model.decoder.layers.{i}.fc1")
        layer_configs = {}
        layer_configs["model.decoder.project_out"] = value
        layer_configs["model.decoder.project_in"] = value
        quantization_config = VptqConfig(config_for_layers=layer_configs, shared_layer_config=shared_layer_config)

        with torch.device("meta"):
            model = AutoModelForCausalLM.from_config(config)

        nb_linears = 0
        for module in model.modules():
            if isinstance(module, torch.nn.Linear):
                nb_linears += 1

        model, _ = replace_with_vptq_linear(model, quantization_config=quantization_config)
        nb_vptq_linear = 0
        for module in model.modules():
            if isinstance(module, VQuantLinear):
                nb_vptq_linear += 1

        self.assertEqual(nb_linears - 1, nb_vptq_linear)

        # Try with `linear_weights_not_to_quantize`
        with torch.device("meta"):
            model = AutoModelForCausalLM.from_config(config)
        quantization_config = VptqConfig(config_for_layers=layer_configs, shared_layer_config=shared_layer_config)
        model, _ = replace_with_vptq_linear(
            model, quantization_config=quantization_config, modules_to_not_convert=modules_to_not_convert
        )
        nb_vptq_linear = 0
        for module in model.modules():
            if isinstance(module, VQuantLinear):
                nb_vptq_linear += 1
        # 25 comes from 24 decoder.layers.{layer_idx}.fc1
        # and the last lm_head
        self.assertEqual(nb_linears - 25, nb_vptq_linear)