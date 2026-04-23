def forward(self, x: Tensor) -> Tensor:
        """ConvModule Forward.

        Args:
            x: input tensor.
        """
        x = self.layer_norm(x)

        if self.ext_pw_out_channel != 0:
            x = self.glu(x)
            if self.causal and self.ext_pw_kernel_size > 1:
                x = x[:, : -(self.ext_pw_kernel_size - 1), :]
            if self.apply_ln1:
                x = self.ln1(x)
        else:
            x_0 = x * self.pw_conv_simplify_w[0] + self.pw_conv_simplify_b[0]
            x_1 = x * self.pw_conv_simplify_w[1] + self.pw_conv_simplify_b[1]
            x = x_0 + x_1

        x = x.permute([0, 2, 1])

        x = self.dw_sep_conv_1d(x)
        if self.causal and self.kernel_size > 1:
            x = x[:, :, : -(self.kernel_size - 1)]
        if hasattr(self, "ln2"):
            x = x.permute([0, 2, 1])
            x = self.ln2(x)
            x = x.permute([0, 2, 1])
        if self.batch_norm:
            x = self.bn_layer(x)
        x = self.act(x)

        if self.ext_pw_out_channel != 0:
            x = self.ext_pw_conv_1d(x)
            if self.fix_len1:
                x = x[:, :, : -(self.ext_pw_kernel_size - 1)]

            if self.apply_ln1:
                x = x.permute([0, 2, 1])
                x = self.ln1(x)
                x = x.permute([0, 2, 1])

            x = x.permute([0, 2, 1])
        else:
            x = x.unsqueeze(1).permute([0, 1, 3, 2])
            x = x * self.pw_conv_simplify_w[2] + self.pw_conv_simplify_b[2]
            x = x.squeeze(1)

        x = self.dropout(x)
        return x