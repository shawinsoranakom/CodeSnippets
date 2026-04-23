def _forward(self, input):
        # exponential_average_factor is self.momentum set to
        # (when it is available) only so that if gets updated
        # in ONNX graph when this node is exported to ONNX.
        if self.momentum is None:
            exponential_average_factor = 0.0
        else:
            exponential_average_factor = self.momentum

        if self.training and not self.freeze_bn and self.track_running_stats:
            # TODO: if statement only here to tell the jit to skip emitting this when it is None
            if self.num_batches_tracked is not None:
                self.num_batches_tracked += 1
                if self.momentum is None:  # use cumulative moving average
                    exponential_average_factor = 1.0 / float(self.num_batches_tracked)
                else:  # use exponential moving average
                    exponential_average_factor = self.momentum

        # we use running statistics from the previous batch, so this is an
        # approximation of the approach mentioned in the whitepaper, but we only
        # need to do one convolution in this case instead of two
        running_std = torch.sqrt(self.running_var + self.eps)
        scale_factor = self.gamma / running_std
        scaled_weight = self.weight * scale_factor.reshape([-1, 1, 1, 1])
        if self.bias is not None:
            zero_bias = torch.zeros_like(self.bias, dtype=input.dtype)
        else:
            zero_bias = torch.zeros(
                self.out_channels, device=scaled_weight.device, dtype=input.dtype
            )
        conv = self._conv_forward(
            input, self.weight_fake_quant(scaled_weight), zero_bias
        )

        if self.training and not self.freeze_bn:
            # recovering original conv to get original batch_mean and batch_var
            if self.bias is not None:
                conv_orig = conv / scale_factor.reshape(
                    [1, -1, 1, 1]
                ) + self.bias.reshape([1, -1, 1, 1])
            else:
                conv_orig = conv / scale_factor.reshape([1, -1, 1, 1])
            batch_mean = torch.mean(conv_orig, dim=[0, 2, 3])
            batch_var = torch.var(conv_orig, dim=[0, 2, 3], unbiased=False)
            n = float(conv_orig.numel() / conv_orig.size()[1])
            unbiased_batch_var = batch_var * (n / (n - 1))
            batch_rstd = torch.ones_like(
                batch_var, memory_format=torch.contiguous_format
            ) / torch.sqrt(batch_var + self.eps)

            conv = (self.gamma * batch_rstd).reshape([1, -1, 1, 1]) * conv_orig + (
                self.beta - self.gamma * batch_rstd * batch_mean
            ).reshape([1, -1, 1, 1])
            self.running_mean = (
                exponential_average_factor * batch_mean.detach()
                + (1 - exponential_average_factor) * self.running_mean
            )
            self.running_var = (
                exponential_average_factor * unbiased_batch_var.detach()
                + (1 - exponential_average_factor) * self.running_var
            )
        else:
            if self.bias is None:
                conv = conv + (
                    self.beta - self.gamma * self.running_mean / running_std
                ).reshape([1, -1, 1, 1])
            else:
                conv = conv + (
                    self.gamma * (self.bias - self.running_mean) / running_std
                    + self.beta
                ).reshape([1, -1, 1, 1])
        return conv