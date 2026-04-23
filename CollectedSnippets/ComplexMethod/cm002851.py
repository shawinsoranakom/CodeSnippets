def forward(
        self,
        encoder_hidden_states: torch.Tensor,
        reference_points: torch.Tensor,
        inputs_embeds: torch.Tensor,
        spatial_shapes,
        level_start_index=None,
        spatial_shapes_list=None,
        encoder_attention_mask=None,
        memory_mask=None,
        **kwargs: Unpack[TransformersKwargs],
    ) -> DFineDecoderOutput:
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
        intermediate_predicted_corners = ()
        initial_reference_points = ()

        output_detach = pred_corners_undetach = 0

        project = weighting_function(self.max_num_bins, self.up, self.reg_scale)
        ref_points_detach = F.sigmoid(reference_points)

        for i, decoder_layer in enumerate(self.layers):
            ref_points_input = ref_points_detach.unsqueeze(2)
            query_pos_embed = self.query_pos_head(ref_points_detach).clamp(min=-10, max=10)

            hidden_states = decoder_layer(
                hidden_states,
                position_embeddings=query_pos_embed,
                reference_points=ref_points_input,
                spatial_shapes=spatial_shapes,
                spatial_shapes_list=spatial_shapes_list,
                encoder_hidden_states=encoder_hidden_states,
                encoder_attention_mask=encoder_attention_mask,
                **kwargs,
            )

            if i == 0:
                # Initial bounding box predictions with inverse sigmoid refinement
                new_reference_points = F.sigmoid(
                    self.pre_bbox_head(hidden_states) + inverse_sigmoid(ref_points_detach)
                )
                ref_points_initial = new_reference_points.detach()

            # Refine bounding box corners using FDR, integrating previous layer's corrections
            if self.bbox_embed is not None:
                pred_corners = self.bbox_embed[i](hidden_states + output_detach) + pred_corners_undetach
                inter_ref_bbox = distance2bbox(
                    ref_points_initial, self.integral(pred_corners, project), self.reg_scale
                )
                pred_corners_undetach = pred_corners
                ref_points_detach = inter_ref_bbox.detach()

            output_detach = hidden_states.detach()

            intermediate += (hidden_states,)

            if self.class_embed is not None and (self.training or i == self.eval_idx):
                scores = self.class_embed[i](hidden_states)
                # Add initial logits and reference points with pre-bbox head
                if i == 0:
                    intermediate_logits += (scores,)
                    intermediate_reference_points += (new_reference_points,)
                # Lqe does not affect the performance here.
                scores = self.lqe_layers[i](scores, pred_corners)
                intermediate_logits += (scores,)
                intermediate_reference_points += (inter_ref_bbox,)
                initial_reference_points += (ref_points_initial,)
                intermediate_predicted_corners += (pred_corners,)

        # Keep batch_size as first dimension
        intermediate = torch.stack(intermediate)
        if self.class_embed is not None and self.bbox_embed is not None:
            intermediate_logits = torch.stack(intermediate_logits, dim=1)
            intermediate_predicted_corners = torch.stack(intermediate_predicted_corners, dim=1)
            initial_reference_points = torch.stack(initial_reference_points, dim=1)
            intermediate_reference_points = torch.stack(intermediate_reference_points, dim=1)

        return DFineDecoderOutput(
            last_hidden_state=hidden_states,
            intermediate_hidden_states=intermediate,
            intermediate_logits=intermediate_logits,
            intermediate_reference_points=intermediate_reference_points,
            intermediate_predicted_corners=intermediate_predicted_corners,
            initial_reference_points=initial_reference_points,
        )