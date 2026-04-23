def __init__(self,  net: network.Network, weights: network.NetworkWeights):

        super().__init__(net, weights)

        self.lin_module = None
        self.org_module: list[torch.Module] = [self.sd_module]

        self.scale = 1.0
        self.is_R = False
        self.is_boft = False

        # kohya-ss/New LyCORIS OFT/BOFT
        if "oft_blocks" in weights.w.keys():
            self.oft_blocks = weights.w["oft_blocks"] # (num_blocks, block_size, block_size)
            self.alpha = weights.w.get("alpha", None) # alpha is constraint
            self.dim = self.oft_blocks.shape[0] # lora dim
        # Old LyCORIS OFT
        elif "oft_diag" in weights.w.keys():
            self.is_R = True
            self.oft_blocks = weights.w["oft_diag"]
            # self.alpha is unused
            self.dim = self.oft_blocks.shape[1] # (num_blocks, block_size, block_size)

        is_linear = type(self.sd_module) in [torch.nn.Linear, torch.nn.modules.linear.NonDynamicallyQuantizableLinear]
        is_conv = type(self.sd_module) in [torch.nn.Conv2d]
        is_other_linear = type(self.sd_module) in [torch.nn.MultiheadAttention] # unsupported

        if is_linear:
            self.out_dim = self.sd_module.out_features
        elif is_conv:
            self.out_dim = self.sd_module.out_channels
        elif is_other_linear:
            self.out_dim = self.sd_module.embed_dim

        # LyCORIS BOFT
        if self.oft_blocks.dim() == 4:
            self.is_boft = True
        self.rescale = weights.w.get('rescale', None)
        if self.rescale is not None and not is_other_linear:
            self.rescale = self.rescale.reshape(-1, *[1]*(self.org_module[0].weight.dim() - 1))

        self.num_blocks = self.dim
        self.block_size = self.out_dim // self.dim
        self.constraint = (0 if self.alpha is None else self.alpha) * self.out_dim
        if self.is_R:
            self.constraint = None
            self.block_size = self.dim
            self.num_blocks = self.out_dim // self.dim
        elif self.is_boft:
            self.boft_m = self.oft_blocks.shape[0]
            self.num_blocks = self.oft_blocks.shape[1]
            self.block_size = self.oft_blocks.shape[2]
            self.boft_b = self.block_size