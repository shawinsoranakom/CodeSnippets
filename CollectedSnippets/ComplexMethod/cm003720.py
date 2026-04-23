def copy_flax_attn_params(hf_backbone, flax_attn_params):
    for k, v in flax_attn_params.items():
        if k.startswith("transformer"):
            torch_key = k.replace("transformer.resblocks", "text_model.encoder.layers")
        else:
            torch_key = k.replace("visual.transformer.resblocks", "vision_model.encoder.layers")

        torch_key = torch_key.replace("attn", "self_attn")
        torch_key = torch_key.replace("key", "k_proj")
        torch_key = torch_key.replace("value", "v_proj")
        torch_key = torch_key.replace("query", "q_proj")
        torch_key = torch_key.replace("out", "out_proj")

        if "bias" in torch_key and v.ndim == 2:
            shape = v.shape[0] * v.shape[1]
            v = v.reshape(shape)

        if "weight" in torch_key and "out" in torch_key:
            shape = (v.shape[0] * v.shape[1], v.shape[2])
            v = v.reshape(shape).T

        if "weight" in torch_key and "out" not in torch_key:
            shape = (v.shape[0], v.shape[1] * v.shape[2])
            v = v.reshape(shape).T

        # Copy flax CLIP attn params to HF PyTorch params
        v = torch.from_numpy(v)
        hf_backbone.state_dict()[torch_key].copy_(v)