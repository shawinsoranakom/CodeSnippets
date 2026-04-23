def convert_state_dict(orig_state_dict, config):
    for key in orig_state_dict.copy():
        val = orig_state_dict.pop(key)

        if "qkv" in key:
            key_split = key.split(".")
            layer_num = int(key_split[1])
            if "decoder_blocks" in key:
                dim = config.decoder_hidden_size
                prefix = "decoder.decoder_layers."
                if "weight" in key:
                    orig_state_dict[f"{prefix}{layer_num}.attention.attention.query.weight"] = val[:dim, :]
                    orig_state_dict[f"{prefix}{layer_num}.attention.attention.key.weight"] = val[dim : dim * 2, :]
                    orig_state_dict[f"{prefix}{layer_num}.attention.attention.value.weight"] = val[-dim:, :]
                elif "bias" in key:
                    orig_state_dict[f"{prefix}{layer_num}.attention.attention.query.bias"] = val[:dim]
                    orig_state_dict[f"{prefix}{layer_num}.attention.attention.key.bias"] = val[dim : dim * 2]
                    orig_state_dict[f"{prefix}{layer_num}.attention.attention.value.bias"] = val[-dim:]
            else:
                dim = config.hidden_size
                prefix = "vit.encoder.layer."
                if "weight" in key:
                    orig_state_dict[f"{prefix}{layer_num}.attention.attention.query.weight"] = val[:dim, :]
                    orig_state_dict[f"{prefix}{layer_num}.attention.attention.key.weight"] = val[dim : dim * 2, :]
                    orig_state_dict[f"{prefix}{layer_num}.attention.attention.value.weight"] = val[-dim:, :]
                elif "bias" in key:
                    orig_state_dict[f"{prefix}{layer_num}.attention.attention.query.bias"] = val[:dim]
                    orig_state_dict[f"{prefix}{layer_num}.attention.attention.key.bias"] = val[dim : dim * 2]
                    orig_state_dict[f"{prefix}{layer_num}.attention.attention.value.bias"] = val[-dim:]

        else:
            orig_state_dict[rename_key(key)] = val

    return orig_state_dict