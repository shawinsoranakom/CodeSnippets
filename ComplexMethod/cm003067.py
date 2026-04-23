def _init_weights(self, module):
        """Initialize the weights"""
        if isinstance(module, EsmFoldLinear):
            with torch.no_grad():
                if module.init_fn is not None:
                    module.init_fn(module.weight, module.bias)
                elif module.init == "default":
                    shape = module.weight.shape
                    scale = 1.0 / max(1, shape[1])
                    std = math.sqrt(scale)
                    init.normal_(module.weight, std=std)
                elif module.init == "relu":
                    shape = module.weight.shape
                    scale = 2.0 / max(1, shape[1])
                    std = math.sqrt(scale)
                    init.normal_(module.weight, std=std)
                elif module.init == "glorot":
                    init.xavier_uniform_(module.weight, gain=1)
                elif module.init == "gating":
                    init.zeros_(module.weight)
                    if module.bias:
                        init.ones_(module.bias)
                elif module.init == "normal":
                    init.kaiming_normal_(module.weight, nonlinearity="linear")
                elif module.init == "final":
                    init.zeros_(module.weight)
        elif isinstance(module, EsmFoldInvariantPointAttention):
            softplus_inverse_1 = 0.541324854612918
            init.constant_(module.head_weights, softplus_inverse_1)
        elif isinstance(module, EsmFoldTriangularSelfAttentionBlock):
            init.zeros_(module.tri_mul_in.linear_z.weight)
            init.zeros_(module.tri_mul_in.linear_z.bias)
            init.zeros_(module.tri_mul_out.linear_z.weight)
            init.zeros_(module.tri_mul_out.linear_z.bias)
            init.zeros_(module.tri_att_start.mha.linear_o.weight)
            init.zeros_(module.tri_att_start.mha.linear_o.bias)
            init.zeros_(module.tri_att_end.mha.linear_o.weight)
            init.zeros_(module.tri_att_end.mha.linear_o.bias)

            init.zeros_(module.sequence_to_pair.o_proj.weight)
            init.zeros_(module.sequence_to_pair.o_proj.bias)
            init.zeros_(module.pair_to_sequence.linear.weight)
            init.zeros_(module.seq_attention.o_proj.weight)
            init.zeros_(module.seq_attention.o_proj.bias)
            init.zeros_(module.mlp_seq.mlp[-2].weight)
            init.zeros_(module.mlp_seq.mlp[-2].bias)
            init.zeros_(module.mlp_pair.mlp[-2].weight)
            init.zeros_(module.mlp_pair.mlp[-2].bias)
        else:
            super()._init_weights(module)