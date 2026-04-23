def forward(self, hidden_states, is_longer_idx=None):
        if self.enable_fusion:
            # retrieve the last mel as we have transposed the input
            global_hidden_states = hidden_states[:, 0:1, :, :]

            # global processing
            batch_size, num_channels, height, width = global_hidden_states.shape

            if height != self.img_size[0] or width != self.img_size[1]:
                raise ValueError(
                    f"Input audio size ({height}*{width}) doesn't match model ({self.img_size[0]}*{self.img_size[1]})."
                )

            global_hidden_states = self.proj(global_hidden_states)
            output_width = global_hidden_states.size(-1)
            if len(is_longer_idx) > 0:
                # local processing
                local_hidden_states = hidden_states[is_longer_idx, 1:, :, :].contiguous()
                batch_size, num_channels, height, width = local_hidden_states.shape
                local_hidden_states = local_hidden_states.view(batch_size * num_channels, 1, height, width)

                local_hidden_states = self.mel_conv2d(local_hidden_states)

                _, features, height, width = local_hidden_states.shape
                local_hidden_states = local_hidden_states.view(batch_size, num_channels, features, height, width)
                local_hidden_states = local_hidden_states.permute((0, 2, 3, 1, 4)).contiguous().flatten(3)

                local_width = local_hidden_states.size(-1)
                local_hidden_states = torch.nn.functional.pad(
                    local_hidden_states, (0, output_width - local_width), "constant", 0
                )

                global_hidden_states[is_longer_idx] = self.fusion_model(
                    global_hidden_states[is_longer_idx], local_hidden_states
                )
            hidden_states = global_hidden_states
        else:
            _, _, height, width = hidden_states.shape
            if height != self.img_size[0] or width != self.img_size[1]:
                raise ValueError(
                    f"Input audio size ({height}*{width}) doesn't match model ({self.img_size[0]}*{self.img_size[1]})."
                )
            hidden_states = self.proj(hidden_states)

        if self.flatten:
            hidden_states = hidden_states.flatten(2).transpose(1, 2)
        hidden_states = self.norm(hidden_states)
        return hidden_states