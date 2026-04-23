def convert_old_quants(state_dict, model_prefix="", metadata={}):
    if metadata is None:
        metadata = {}

    quant_metadata = None
    if "_quantization_metadata" not in metadata:
        scaled_fp8_key = "{}scaled_fp8".format(model_prefix)

        if scaled_fp8_key in state_dict:
            scaled_fp8_weight = state_dict[scaled_fp8_key]
            scaled_fp8_dtype = scaled_fp8_weight.dtype
            if scaled_fp8_dtype == torch.float32:
                scaled_fp8_dtype = torch.float8_e4m3fn

            if scaled_fp8_weight.nelement() == 2:
                full_precision_matrix_mult = True
            else:
                full_precision_matrix_mult = False

            out_sd = {}
            layers = {}
            for k in list(state_dict.keys()):
                if k == scaled_fp8_key:
                    continue
                if not k.startswith(model_prefix):
                    out_sd[k] = state_dict[k]
                    continue
                k_out = k
                w = state_dict.pop(k)
                layer = None
                if k_out.endswith(".scale_weight"):
                    layer = k_out[:-len(".scale_weight")]
                    k_out = "{}.weight_scale".format(layer)

                if layer is not None:
                    layer_conf = {"format": "float8_e4m3fn"}  # TODO: check if anyone did some non e4m3fn scaled checkpoints
                    if full_precision_matrix_mult:
                        layer_conf["full_precision_matrix_mult"] = full_precision_matrix_mult
                    layers[layer] = layer_conf

                if k_out.endswith(".scale_input"):
                    layer = k_out[:-len(".scale_input")]
                    k_out = "{}.input_scale".format(layer)
                    if w.item() == 1.0:
                        continue

                out_sd[k_out] = w

            state_dict = out_sd
            quant_metadata = {"layers": layers}
    else:
        quant_metadata = json.loads(metadata["_quantization_metadata"])

    if quant_metadata is not None:
        layers = quant_metadata["layers"]
        for k, v in layers.items():
            state_dict["{}.comfy_quant".format(k)] = torch.tensor(list(json.dumps(v).encode('utf-8')), dtype=torch.uint8)

    return state_dict, metadata