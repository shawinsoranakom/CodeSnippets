def forward(
        self,
        inputs_embeds=None,
        encoder_hidden_states=None,
        encoder_attention_mask=None,
        reference_points=None,
        spatial_shapes=None,
        spatial_shapes_list=None,
        level_start_index=None,
        order_head=None,
        global_pointer=None,
        mask_query_head=None,
        norm=None,
        mask_feat=None,
        **kwargs: Unpack[TransformersKwargs],
    ):
        r"""
        Args:
            inputs_embeds (`torch.FloatTensor` of shape `(batch_size, num_queries, hidden_size)`):
                The query embeddings that are passed into the decoder.
            encoder_hidden_states (`torch.FloatTensor` of shape `(batch_size, sequence_length, hidden_size)`, *optional*):
                Sequence of hidden-states at the output of the last layer of the encoder. Used in the cross-attention
                of the decoder.
            encoder_attention_mask (`torch.LongTensor` of shape `(batch_size, sequence_length)`, *optional*):
                Mask to avoid performing cross-attention on padding pixel_values of the encoder. Mask values selected
                in `[0, 1]`:
                - 1 for pixels that are real (i.e. **not masked**),
                - 0 for pixels that are padding (i.e. **masked**).
            reference_points (`torch.FloatTensor` of shape `(batch_size, num_queries, 4)` is `as_two_stage` else `(batch_size, num_queries, 2)` or , *optional*):
                Reference point in range `[0, 1]`, top-left (0,0), bottom-right (1, 1), including padding area.
            spatial_shapes (`torch.FloatTensor` of shape `(num_feature_levels, 2)`):
                Spatial shapes of the feature maps.
            level_start_index (`torch.LongTensor` of shape `(num_feature_levels)`, *optional*):
                Indexes for the start of each feature level. In range `[0, sequence_length]`.
        """
        if inputs_embeds is not None:
            hidden_states = inputs_embeds

        # decoder layers
        intermediate = ()
        intermediate_reference_points = ()
        intermediate_logits = ()
        decoder_out_order_logits = ()
        decoder_out_masks = ()

        reference_points = F.sigmoid(reference_points)

        # https://github.com/lyuwenyu/RT-DETR/blob/94f5e16708329d2f2716426868ec89aa774af016/rtdetr_pytorch/src/zoo/rtdetr/rtdetr_decoder.py#L252
        for idx, decoder_layer in enumerate(self.layers):
            reference_points_input = reference_points.unsqueeze(2)
            object_queries_position_embeddings = self.query_pos_head(reference_points)

            hidden_states = decoder_layer(
                hidden_states,
                object_queries_position_embeddings=object_queries_position_embeddings,
                encoder_hidden_states=encoder_hidden_states,
                reference_points=reference_points_input,
                spatial_shapes=spatial_shapes,
                spatial_shapes_list=spatial_shapes_list,
                level_start_index=level_start_index,
                encoder_attention_mask=encoder_attention_mask,
                **kwargs,
            )

            # hack implementation for iterative bounding box refinement
            if self.bbox_embed is not None:
                predicted_corners = self.bbox_embed(hidden_states)
                new_reference_points = F.sigmoid(predicted_corners + inverse_sigmoid(reference_points))
                reference_points = new_reference_points.detach()

            intermediate += (hidden_states,)
            intermediate_reference_points += (
                (new_reference_points,) if self.bbox_embed is not None else (reference_points,)
            )

            # get_pred_class_order_and_mask
            out_query = norm(hidden_states)
            mask_query_embed = mask_query_head(out_query)
            batch_size, mask_dim, _ = mask_query_embed.shape
            _, _, mask_h, mask_w = mask_feat.shape
            out_mask = torch.bmm(mask_query_embed, mask_feat.flatten(start_dim=2)).reshape(
                batch_size, mask_dim, mask_h, mask_w
            )
            decoder_out_masks += (out_mask,)

            if self.class_embed is not None:
                logits = self.class_embed(out_query)
                intermediate_logits += (logits,)

            if order_head is not None and global_pointer is not None:
                valid_query = out_query[:, -self.num_queries :] if self.num_queries is not None else out_query
                order_logits = global_pointer(order_head[idx](valid_query))
                decoder_out_order_logits += (order_logits,)

        # Keep batch_size as first dimension
        intermediate = torch.stack(intermediate, dim=1)
        intermediate_reference_points = torch.stack(intermediate_reference_points, dim=1)
        if self.class_embed is not None:
            intermediate_logits = torch.stack(intermediate_logits, dim=1)
        if order_head is not None and global_pointer is not None:
            decoder_out_order_logits = torch.stack(decoder_out_order_logits, dim=1)
        decoder_out_masks = torch.stack(decoder_out_masks, dim=1)

        return PPDocLayoutV3DecoderOutput(
            last_hidden_state=hidden_states,
            intermediate_hidden_states=intermediate,
            intermediate_logits=intermediate_logits,
            intermediate_reference_points=intermediate_reference_points,
            decoder_out_order_logits=decoder_out_order_logits,
            decoder_out_masks=decoder_out_masks,
        )