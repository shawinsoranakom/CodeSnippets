def forward(
        self,
        inputs_embeddings=None,
        output_attentions=None,
        output_hidden_states=None,
        return_dict=None,
    ):
        r"""
        Args:
            inputs_embeddings (`torch.FloatTensor` of shape `(batch_size, sequence_length, hidden_size)`):
                Flattened feature map (output of the backbone + projection layers) that is passed to the encoder.
            output_attentions (`bool`, *optional*):
                Whether or not to return the attentions tensors of all attention layers. See `attentions` under
                returned tensors for more detail.
            output_hidden_states (`bool`, *optional*):
                Whether or not to return the hidden states of all layers. See `hidden_states` under returned tensors
                for more detail.
            return_dict (`bool`, *optional*):
                Whether or not to return a [`~file_utils.ModelOutput`] instead of a plain tuple.
        """
        output_attentions = output_attentions if output_attentions is not None else self.config.output_attentions
        output_hidden_states = (
            output_hidden_states if output_hidden_states is not None else self.config.output_hidden_states
        )
        return_dict = return_dict if return_dict is not None else self.config.return_dict

        hidden_states = inputs_embeddings

        encoder_states = () if output_hidden_states else None
        all_attentions = () if output_attentions else None
        # get projection features
        projected_features = [self.channel_projection_layers[i](feature) for i, feature in enumerate(hidden_states)]
        # encoder
        for encoder_layer_index, feature_to_project_index in enumerate(self.encoder_projection_indices):
            if output_hidden_states:
                encoder_states = encoder_states + (projected_features[feature_to_project_index],)
            height, width = projected_features[feature_to_project_index].shape[2:]
            # flatten [batch, channel, height, width] to [batch, height*width, channel]
            src_flatten = projected_features[feature_to_project_index].flatten(2).permute(0, 2, 1)
            if self.training or self.eval_size is None:
                pos_embed = self.build_2d_sincos_position_embedding(
                    width,
                    height,
                    self.encoder_hidden_dim,
                    self.positional_encoding_temperature,
                    device=src_flatten.device,
                    dtype=src_flatten.dtype,
                ).to(src_flatten.device, src_flatten.dtype)
            else:
                pos_embed = None
            layer_outputs = self.encoder[encoder_layer_index](
                src_flatten,
                pos_embed=pos_embed,
                output_attentions=output_attentions,
            )
            projected_features[feature_to_project_index] = (
                layer_outputs[0].permute(0, 2, 1).reshape(-1, self.encoder_hidden_dim, height, width).contiguous()
            )

            if output_attentions:
                all_attentions = all_attentions + (layer_outputs[1],)

        if output_hidden_states:
            encoder_states = encoder_states + (projected_features[feature_to_project_index],)

        # Feature Pyramid Network (FPN)
        fpn_feature_maps = [projected_features[-1]]
        for idx in range(len(self.in_channels) - 1, 0, -1):
            feat_high = fpn_feature_maps[0]
            feat_low = projected_features[idx - 1]
            feat_high = self.lateral_convs[len(self.in_channels) - 1 - idx](feat_high)
            fpn_feature_maps[0] = feat_high
            upsample_feat = F.interpolate(feat_high, scale_factor=2.0, mode="nearest")
            fps_map = self.fpn_blocks[len(self.in_channels) - 1 - idx](torch.concat([upsample_feat, feat_low], dim=1))
            fpn_feature_maps.insert(0, fps_map)

        # Path Aggregation Network (PAN)
        fpn_states = [fpn_feature_maps[0]]
        for idx in range(len(self.in_channels) - 1):
            feat_low = fpn_states[-1]
            feat_high = fpn_feature_maps[idx + 1]
            downsample_feat = self.downsample_convs[idx](feat_low)
            hidden_states = self.pan_blocks[idx](
                torch.concat([downsample_feat, feat_high.to(downsample_feat.device)], dim=1)
            )
            fpn_states.append(hidden_states)
        if not return_dict:
            return (fpn_states[-1], encoder_states, all_attentions, fpn_states)
        return OmDetTurboEncoderOutput(
            last_hidden_state=fpn_states[-1],
            hidden_states=encoder_states,
            attentions=all_attentions,
            extracted_states=fpn_states,
        )