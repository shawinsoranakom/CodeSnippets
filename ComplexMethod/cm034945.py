def __init__(self, inp, hidden_dim, oup, kernel_size, stride, use_se, use_hs):
        super(RepViTBlock, self).__init__()

        self.identity = stride == 1 and inp == oup
        assert hidden_dim == 2 * inp

        if stride != 1:
            self.token_mixer = nn.Sequential(
                Conv2D_BN(
                    inp, inp, kernel_size, stride, (kernel_size - 1) // 2, groups=inp
                ),
                SEModule(inp, 0.25) if use_se else nn.Identity(),
                Conv2D_BN(inp, oup, ks=1, stride=1, pad=0),
            )
            self.channel_mixer = Residual(
                nn.Sequential(
                    # pw
                    Conv2D_BN(oup, 2 * oup, 1, 1, 0),
                    nn.GELU() if use_hs else nn.GELU(),
                    # pw-linear
                    Conv2D_BN(2 * oup, oup, 1, 1, 0, bn_weight_init=0),
                )
            )
        else:
            assert self.identity
            self.token_mixer = nn.Sequential(
                RepVGGDW(inp),
                SEModule(inp, 0.25) if use_se else nn.Identity(),
            )
            self.channel_mixer = Residual(
                nn.Sequential(
                    # pw
                    Conv2D_BN(inp, hidden_dim, 1, 1, 0),
                    nn.GELU() if use_hs else nn.GELU(),
                    # pw-linear
                    Conv2D_BN(hidden_dim, oup, 1, 1, 0, bn_weight_init=0),
                )
            )