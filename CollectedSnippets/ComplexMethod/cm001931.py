def _mock_init_weights(self, module):
        if hasattr(module, "weight") and module.weight is not None:
            module.weight.fill_(3)
        if hasattr(module, "weight_g") and module.weight_g is not None:
            module.weight_g.data.fill_(3)
        if hasattr(module, "weight_v") and module.weight_v is not None:
            module.weight_v.data.fill_(3)
        if hasattr(module, "bias") and module.bias is not None:
            module.bias.fill_(3)
        if hasattr(module, "pos_bias_u") and module.pos_bias_u is not None:
            module.pos_bias_u.data.fill_(3)
        if hasattr(module, "pos_bias_v") and module.pos_bias_v is not None:
            module.pos_bias_v.data.fill_(3)
        if hasattr(module, "codevectors") and module.codevectors is not None:
            module.codevectors.data.fill_(3)
        if hasattr(module, "masked_spec_embed") and module.masked_spec_embed is not None:
            module.masked_spec_embed.data.fill_(3)