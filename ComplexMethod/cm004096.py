def forward(
        self,
        input_features,
        is_longer: torch.FloatTensor | None = None,
        output_attentions: bool | None = False,
        output_hidden_states: bool | None = False,
        output_hidden_states_before_downsampling: bool | None = False,
        always_partition: bool | None = False,
        return_dict: bool | None = True,
    ) -> tuple | ClapAudioModelOutput:
        # Unique logic so no refactor here yet
        output_hidden_states = output_hidden_states or self.config.output_hidden_states
        output_attentions = output_attentions or self.config.output_attentions

        input_features = input_features.transpose(1, 3)
        normalized_input_features = self.batch_norm(input_features)
        normalized_input_features = normalized_input_features.transpose(1, 3)

        is_longer_list_idx = None
        if self.enable_fusion:
            is_longer_list = is_longer.to(input_features.device)
            is_longer_list_idx = torch.where(is_longer_list == 1)[0]

        hidden_states = self.reshape_mel2img(normalized_input_features)

        frames_num = hidden_states.shape[2]

        hidden_states = self.patch_embed(hidden_states, is_longer_list_idx)

        all_hidden_states = () if output_hidden_states else None
        all_reshaped_hidden_states = () if output_hidden_states else None
        all_self_attentions = () if output_attentions else None

        input_dimensions = self.input_resolutions[0]

        if output_hidden_states:
            batch_size, _, hidden_size = hidden_states.shape
            # rearrange batch_size (height width) channels -> batch_size channel height width
            reshaped_hidden_state = hidden_states.view(batch_size, *input_dimensions, hidden_size)
            reshaped_hidden_state = reshaped_hidden_state.permute(0, 3, 1, 2)
            all_hidden_states += (hidden_states,)
            all_reshaped_hidden_states += (reshaped_hidden_state,)

        for i, layer_module in enumerate(self.layers):
            input_dimensions = self.input_resolutions[i]

            layer_outputs = layer_module(hidden_states, input_dimensions, output_attentions, always_partition)

            hidden_states = layer_outputs[0]

            hidden_states_before_downsampling = layer_outputs[1]
            output_dimensions = layer_outputs[2]

            input_dimensions = (output_dimensions[-2], output_dimensions[-1])

            if output_hidden_states and output_hidden_states_before_downsampling:
                batch_size, _, hidden_size = hidden_states_before_downsampling.shape
                # rearrange batch_size (height width) channels -> batch_size channel height width
                # here we use the original (not downsampled) height and width
                reshaped_hidden_state = hidden_states_before_downsampling.view(
                    batch_size, *(output_dimensions[0], output_dimensions[1]), hidden_size
                )
                reshaped_hidden_state = reshaped_hidden_state.permute(0, 3, 1, 2)
                all_hidden_states += (hidden_states_before_downsampling,)
                all_reshaped_hidden_states += (reshaped_hidden_state,)
            elif output_hidden_states and not output_hidden_states_before_downsampling:
                batch_size, _, hidden_size = hidden_states.shape
                # rearrange batch_size (height width) channels -> batch_size channel height width
                reshaped_hidden_state = hidden_states.view(batch_size, *input_dimensions, hidden_size)
                reshaped_hidden_state = reshaped_hidden_state.permute(0, 3, 1, 2)
                all_hidden_states += (hidden_states,)
                all_reshaped_hidden_states += (reshaped_hidden_state,)

            if output_attentions:
                all_self_attentions += layer_outputs[3:]

        last_hidden_state = self.norm(hidden_states)

        batch_size, _, n_channels = last_hidden_state.shape

        freq_shape = frames_num // (2 ** (len(self.depths) - 1)) // self.patch_stride[0]
        temporal_shape = frames_num // (2 ** (len(self.depths) - 1)) // self.patch_stride[1]

        last_hidden_state = (
            last_hidden_state.permute(0, 2, 1).contiguous().reshape(batch_size, n_channels, freq_shape, temporal_shape)
        )

        batch_size, n_channels, n_frequencies, n_temp = last_hidden_state.shape
        # group 2D CNN
        c_freq_bin = n_frequencies // self.freq_ratio
        last_hidden_state = last_hidden_state.reshape(
            batch_size, n_channels, n_frequencies // c_freq_bin, c_freq_bin, n_temp
        )
        last_hidden_state = (
            last_hidden_state.permute(0, 1, 3, 2, 4).contiguous().reshape(batch_size, n_channels, c_freq_bin, -1)
        )
        latent_output = self.avgpool(torch.flatten(last_hidden_state, 2))
        latent_output = torch.flatten(latent_output, 1)

        return BaseModelOutputWithPooling(
            last_hidden_state=last_hidden_state,
            pooler_output=latent_output,
            hidden_states=all_reshaped_hidden_states,
            attentions=all_self_attentions,
        )