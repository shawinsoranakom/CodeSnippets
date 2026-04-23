def calc_lora_model(model_diff, rank, prefix_model, prefix_lora, output_sd, lora_type, bias_diff=False):
    comfy.model_management.load_models_gpu([model_diff])
    sd = model_diff.model_state_dict(filter_prefix=prefix_model)

    sd_keys = list(sd.keys())
    for index in trange(len(sd_keys), unit="weight"):
        k = sd_keys[index]
        op_keys = sd_keys[index].rsplit('.', 1)
        if len(op_keys) < 2 or op_keys[1] not in ["weight", "bias"] or (op_keys[1] == "bias" and not bias_diff):
            continue
        op = comfy.utils.get_attr(model_diff.model, op_keys[0])
        if hasattr(op, "comfy_cast_weights") and not getattr(op, "comfy_patched_weights", False):
            weight_diff = model_diff.patch_weight_to_device(k, model_diff.load_device, return_weight=True)
        else:
            weight_diff = sd[k]

        if op_keys[1] == "weight":
            if lora_type == LORAType.STANDARD:
                if weight_diff.ndim < 2:
                    if bias_diff:
                        output_sd["{}{}.diff".format(prefix_lora, k[len(prefix_model):-7])] = weight_diff.contiguous().half().cpu()
                    continue
                try:
                    out = extract_lora(weight_diff, rank)
                    output_sd["{}{}.lora_up.weight".format(prefix_lora, k[len(prefix_model):-7])] = out[0].contiguous().half().cpu()
                    output_sd["{}{}.lora_down.weight".format(prefix_lora, k[len(prefix_model):-7])] = out[1].contiguous().half().cpu()
                except:
                    logging.warning("Could not generate lora weights for key {}, is the weight difference a zero?".format(k))
            elif lora_type == LORAType.FULL_DIFF:
                output_sd["{}{}.diff".format(prefix_lora, k[len(prefix_model):-7])] = weight_diff.contiguous().half().cpu()

        elif bias_diff and op_keys[1] == "bias":
            output_sd["{}{}.diff_b".format(prefix_lora, k[len(prefix_model):-5])] = weight_diff.contiguous().half().cpu()
    return output_sd