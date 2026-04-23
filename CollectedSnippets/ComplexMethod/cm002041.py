def _mock_init_weights(self, module):
        if hasattr(module, "weight") and module.weight is not None:
            module.weight.fill_(3)
        if hasattr(module, "bias") and module.bias is not None:
            module.bias.fill_(3)

        for param in ["q", "k", "v", "o", "r", "r_r_bias", "r_s_bias", "r_w_bias", "seg_embed", "mask_emb"]:
            if hasattr(module, param) and getattr(module, param) is not None:
                weight = getattr(module, param)
                weight.data.fill_(3)