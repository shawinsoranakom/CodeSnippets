def rename_fairseq_keys(state_dict, expert_idx=None):
    new_dict = {}
    for old_key in state_dict:
        key = old_key
        if "moe_layer.experts." in key:
            if expert_idx is not None:
                key = key.replace("moe_layer.experts.0", f"ffn.experts.expert_{expert_idx}")
            else:
                key = key.replace("moe_layer.experts.", "ffn.experts.expert_")
        if "gate" in key:
            key = key.replace(".moe_layer.gate.wg", ".ffn.router.classifier")
        if "fc2" and "experts" not in key:
            key = key.replace(".fc2.", ".ffn.fc2.")
        if "fc1" and "experts" not in key:
            key = key.replace(".fc1.", ".ffn.fc1.")
        if ".encoder_attn." in key:
            key = key.replace(".encoder_attn.", ".cross_attention.")
        if "encoder_attn_layer_norm" in key:
            key = key.replace("encoder_attn_layer_norm", "cross_attention_layer_norm")
        if "final_layer_norm" in key:
            key = key.replace("final_layer_norm", "ff_layer_norm")
        new_dict[key] = state_dict[old_key]
    return new_dict