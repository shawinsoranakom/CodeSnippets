def forward(self, x):
        """
        Forward pass of the vocoder.

        Args:
            x: Input spectrogram tensor. Can be:
               - 3D: (batch_size, channels, time_steps) for mono
               - 4D: (batch_size, 2, channels, time_steps) for stereo

        Returns:
            Audio tensor of shape (batch_size, out_channels, audio_length)
        """
        if x.dim() == 4:  # stereo
            assert x.shape[1] == 2, "Input must have 2 channels for stereo"
            x = torch.cat((x[:, 0, :, :], x[:, 1, :, :]), dim=1)
        x = self.conv_pre(x)

        for i in range(self.num_upsamples):
            if self.resblock != "AMP1":
                x = F.leaky_relu(x, LRELU_SLOPE)
            x = self.ups[i](x)
            xs = None
            for j in range(self.num_kernels):
                if xs is None:
                    xs = self.resblocks[i * self.num_kernels + j](x)
                else:
                    xs += self.resblocks[i * self.num_kernels + j](x)
            x = xs / self.num_kernels

        x = self.act_post(x)
        x = self.conv_post(x)

        if self.apply_final_activation:
            if self.use_tanh_at_final:
                x = torch.tanh(x)
            else:
                x = torch.clamp(x, -1, 1)

        return x