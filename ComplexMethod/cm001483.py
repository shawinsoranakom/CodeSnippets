def __init__(self, net: Network, weights: NetworkWeights):
        self.network = net
        self.network_key = weights.network_key
        self.sd_key = weights.sd_key
        self.sd_module = weights.sd_module

        if isinstance(self.sd_module, modules.models.sd3.mmdit.QkvLinear):
            s = self.sd_module.weight.shape
            self.shape = (s[0] // 3, s[1])
        elif hasattr(self.sd_module, 'weight'):
            self.shape = self.sd_module.weight.shape
        elif isinstance(self.sd_module, nn.MultiheadAttention):
            # For now, only self-attn use Pytorch's MHA
            # So assume all qkvo proj have same shape
            self.shape = self.sd_module.out_proj.weight.shape
        else:
            self.shape = None

        self.ops = None
        self.extra_kwargs = {}
        if isinstance(self.sd_module, nn.Conv2d):
            self.ops = F.conv2d
            self.extra_kwargs = {
                'stride': self.sd_module.stride,
                'padding': self.sd_module.padding
            }
        elif isinstance(self.sd_module, nn.Linear):
            self.ops = F.linear
        elif isinstance(self.sd_module, nn.LayerNorm):
            self.ops = F.layer_norm
            self.extra_kwargs = {
                'normalized_shape': self.sd_module.normalized_shape,
                'eps': self.sd_module.eps
            }
        elif isinstance(self.sd_module, nn.GroupNorm):
            self.ops = F.group_norm
            self.extra_kwargs = {
                'num_groups': self.sd_module.num_groups,
                'eps': self.sd_module.eps
            }

        self.dim = None
        self.bias = weights.w.get("bias")
        self.alpha = weights.w["alpha"].item() if "alpha" in weights.w else None
        self.scale = weights.w["scale"].item() if "scale" in weights.w else None

        self.dora_scale = weights.w.get("dora_scale", None)
        self.dora_norm_dims = len(self.shape) - 1