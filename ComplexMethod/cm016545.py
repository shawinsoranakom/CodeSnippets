def __init__(self, device="cpu", max_length=77,
                 freeze=True, layer="last", layer_idx=None, textmodel_json_config=None, dtype=None, model_class=comfy.clip_model.CLIPTextModel,
                 special_tokens={"start": 49406, "end": 49407, "pad": 49407}, layer_norm_hidden_state=True, enable_attention_masks=False, zero_out_masked=False,
                 return_projected_pooled=True, return_attention_masks=False, model_options={}):  # clip-vit-base-patch32
        super().__init__()

        if textmodel_json_config is None:
            textmodel_json_config = os.path.join(os.path.dirname(os.path.realpath(__file__)), "sd1_clip_config.json")
            if "model_name" not in model_options:
                model_options = {**model_options, "model_name": "clip_l"}

        if isinstance(textmodel_json_config, dict):
            config = textmodel_json_config
        else:
            with open(textmodel_json_config) as f:
                config = json.load(f)

        te_model_options = model_options.get("{}_model_config".format(model_options.get("model_name", "")), {})
        for k, v in te_model_options.items():
            config[k] = v

        operations = model_options.get("custom_operations", None)
        quant_config = model_options.get("quantization_metadata", None)

        if operations is None:
            if quant_config is not None:
                operations = comfy.ops.mixed_precision_ops(quant_config, dtype, full_precision_mm=True)
                logging.info("Using MixedPrecisionOps for text encoder")
            else:
                operations = comfy.ops.manual_cast

        self.operations = operations
        self.transformer = model_class(config, dtype, device, self.operations)

        self.num_layers = self.transformer.num_layers

        self.max_length = max_length
        if freeze:
            self.freeze()
        self.layer = layer
        self.layer_idx = None
        self.special_tokens = special_tokens

        self.logit_scale = torch.nn.Parameter(torch.tensor(4.6055))
        self.enable_attention_masks = enable_attention_masks
        self.zero_out_masked = zero_out_masked

        self.layer_norm_hidden_state = layer_norm_hidden_state
        self.return_projected_pooled = return_projected_pooled
        self.return_attention_masks = return_attention_masks
        self.execution_device = None

        if layer == "hidden":
            assert layer_idx is not None
            assert abs(layer_idx) < self.num_layers
            self.set_clip_options({"layer": layer_idx})
        self.options_default = (self.layer, self.layer_idx, self.return_projected_pooled)