def _init_weights(self, module):
        """Initialize the weights"""
        if isinstance(module, nn.GroupNorm):
            init.zeros_(module.bias)
            init.ones_(module.weight)
        elif isinstance(module, nn.Conv1d):
            init.kaiming_normal_(module.weight)
            if module.bias is not None:
                k = math.sqrt(module.groups / (module.in_channels * module.kernel_size[0]))
                init.uniform_(module.bias, a=-k, b=k)
        elif isinstance(module, nn.ConvTranspose1d):
            module.reset_parameters()
        elif isinstance(module, nn.LSTM):
            for name, param in module.named_parameters():
                if "weight" in name:
                    init.xavier_uniform_(param)
                elif "bias" in name:
                    init.constant_(param, 0.0)
        elif isinstance(module, EncodecConv1d):
            kernel_size = module.conv.kernel_size[0]
            stride = torch.tensor(module.conv.stride[0], dtype=torch.int64)
            dilation = module.conv.dilation[0]
            # Effective kernel size with dilations.
            kernel_size = torch.tensor((kernel_size - 1) * dilation + 1, dtype=torch.int64)
            init.copy_(module.stride, stride)
            init.copy_(module.kernel_size, kernel_size)
            init.copy_(module.padding_total, kernel_size - stride)
        elif isinstance(module, EncodecEuclideanCodebook):
            init.copy_(module.inited, torch.Tensor([True]))
            init.zeros_(module.cluster_size)
            init.zeros_(module.embed)
            init.zeros_(module.embed_avg)