def forward(self, x: Tensor, mask: Tensor | None) -> tuple[Tensor, Tensor | None]:
        """
        Forward method for NeMo subsampling.

        Args:
            x: input tensor
            mask: input mask

        Returns:
            x: Resulting tensor from subsampling (B, T //
                time_reduction_factor, feat_out)
            pad_mask: tensor of padded hidden state sequences (B, 1, T //
                time_reduction_factor)
        """
        x = x.unsqueeze(1) if self.conv2d_subsampling else x.transpose(1, 2)

        # split inputs if chunking_factor is set
        if self.subsampling_conv_chunking_factor != -1 and self.conv2d_subsampling:
            if self.subsampling_conv_chunking_factor == 1:
                # if subsampling_conv_chunking_factor is 1, we split only
                # if needed.
                # avoiding a bug / feature limiting indexing of tensors
                # to 2**31.
                # see https://github.com/pytorch/pytorch/issues/80020
                x_ceil = 2**31 / self._conv_channels * self._stride * self._stride
                need_to_split = torch.numel(x) > x_ceil
            else:
                # if subsampling_conv_chunking_factor > 1 we always split
                need_to_split = True

            if need_to_split:
                x, success = self.conv_split_by_batch(x)
                if not success:  # if unable to split by batch, try by channel
                    if self._subsampling == "dw_striding":
                        x = self.conv_split_by_channel(x)
                    else:
                        x = self.conv(x)  # try anyway
            else:
                x = self.conv(x)
        else:
            x = self.conv(x)

        # Flatten Channel and Frequency Axes
        if self.conv2d_subsampling:
            b, c, t, f = x.size()
            x = self.out(x.transpose(1, 2).reshape(b, t, -1))
        # Transpose to Channel Last mode
        else:
            x = x.transpose(1, 2)

        if mask is None:
            return x, None

        max_audio_length = x.shape[1]
        feature_lens = mask.sum(1)
        padding_length = torch.ceil(feature_lens / self.subsampling_factor)
        if self.is_causal and self.subsampling_causal_cond:
            feature_lens_remainder = feature_lens % self.subsampling_factor
            padding_length[feature_lens_remainder != 1] += 1
        pad_mask = torch.arange(0, max_audio_length, device=x.device).expand(
            padding_length.size(0), -1
        ) < padding_length.unsqueeze(1)
        return x, pad_mask.unsqueeze(1)