def forward(
        self,
        features,
        encoder_outputs=None,
        output_attentions=None,
        output_hidden_states=None,
        return_dict=None,
    ):
        output_attentions = output_attentions if output_attentions is not None else self.config.output_attentions
        output_hidden_states = (
            output_hidden_states if output_hidden_states is not None else self.config.output_hidden_states
        )

        # Apply 1x1 convolution to reduce the channel dimension to d_model (256 by default)
        inputs_embeds = []
        position_embeddings = []
        for level, x in enumerate(features[::-1][: self.num_feature_levels]):
            inputs_embeds.append(self.input_projections[level](x))
            position_embeddings.append(self.position_embedding(x.shape, x.device, x.dtype))

        masks = [
            torch.zeros((x.size(0), x.size(2), x.size(3)), device=x.device, dtype=torch.bool) for x in inputs_embeds
        ]

        # Prepare encoder inputs (by flattening)
        spatial_shapes_list = [(embed.shape[2], embed.shape[3]) for embed in inputs_embeds]
        input_embeds_flat = torch.cat([embed.flatten(2).transpose(1, 2) for embed in inputs_embeds], 1)
        spatial_shapes = torch.as_tensor(spatial_shapes_list, dtype=torch.long, device=input_embeds_flat.device)
        masks_flat = torch.cat([mask.flatten(1) for mask in masks], 1)

        position_embeddings = [embed.flatten(2).transpose(1, 2) for embed in position_embeddings]
        level_pos_embed_flat = [x + self.level_embed[i].view(1, 1, -1) for i, x in enumerate(position_embeddings)]
        level_pos_embed_flat = torch.cat(level_pos_embed_flat, 1)

        level_start_index = torch.cat((spatial_shapes.new_zeros((1,)), spatial_shapes.prod(1).cumsum(0)[:-1]))
        valid_ratios = torch.stack([self.get_valid_ratio(mask, dtype=input_embeds_flat.dtype) for mask in masks], 1)

        # Send input_embeds_flat + masks_flat + level_pos_embed_flat (backbone + proj layer output) through encoder
        if encoder_outputs is None:
            encoder_outputs = self.encoder(
                inputs_embeds=input_embeds_flat,
                attention_mask=masks_flat,
                position_embeddings=level_pos_embed_flat,
                spatial_shapes_list=spatial_shapes_list,
                level_start_index=level_start_index,
                valid_ratios=valid_ratios,
                output_attentions=output_attentions,
                output_hidden_states=output_hidden_states,
                return_dict=return_dict,
            )

        last_hidden_state = encoder_outputs.last_hidden_state
        batch_size = last_hidden_state.shape[0]

        # We compute level_start_index_list separately from the tensor version level_start_index
        # to avoid iterating over a tensor which breaks torch.compile/export.
        level_start_index_list = [0]
        for height, width in spatial_shapes_list[:-1]:
            level_start_index_list.append(level_start_index_list[-1] + height * width)
        split_sizes = [None] * self.num_feature_levels
        for i in range(self.num_feature_levels):
            if i < self.num_feature_levels - 1:
                split_sizes[i] = level_start_index_list[i + 1] - level_start_index_list[i]
            else:
                split_sizes[i] = last_hidden_state.shape[1] - level_start_index_list[i]

        encoder_output = torch.split(last_hidden_state, split_sizes, dim=1)

        # Compute final features
        outputs = [
            x.transpose(1, 2).view(batch_size, -1, spatial_shapes_list[i][0], spatial_shapes_list[i][1])
            for i, x in enumerate(encoder_output)
        ]

        # Append extra FPN levels to outputs, ordered from low to high resolution
        for idx, feature in enumerate(features[: self.num_fpn_levels][::-1]):
            lateral_conv = self.lateral_convolutions[idx]
            output_conv = self.output_convolutions[idx]
            current_fpn = lateral_conv(feature)

            # Following FPN implementation, we use nearest upsampling here
            out = current_fpn + nn.functional.interpolate(
                outputs[-1], size=current_fpn.shape[-2:], mode="bilinear", align_corners=False
            )
            out = output_conv(out)
            outputs.append(out)

        num_cur_levels = 0
        multi_scale_features = []

        for out in outputs:
            if num_cur_levels < self.num_feature_levels:
                multi_scale_features.append(out)
                num_cur_levels += 1

        return Mask2FormerPixelDecoderOutput(
            mask_features=self.mask_projection(outputs[-1]),
            multi_scale_features=tuple(multi_scale_features),
            attentions=encoder_outputs.attentions,
        )