def _mock_init_weights(self, module):
        if hasattr(module, "weight") and module.weight is not None:
            module.weight.fill_(3)
        if hasattr(module, "bias") and module.bias is not None:
            module.bias.fill_(3)

        for param in ["r_w_bias", "r_r_bias", "r_kernel", "r_s_bias", "seg_embed"]:
            if hasattr(module, param) and getattr(module, param) is not None:
                weight = getattr(module, param)
                weight.data.fill_(3)