def forward(
        self,
        tgt,
        memory,
        tgt_mask: torch.Tensor = None,
        memory_mask: torch.Tensor = None,
        memory_key_padding_mask: torch.Tensor = None,
        pos: torch.Tensor = None,
        reference_boxes: torch.Tensor = None,  # num_queries, bs, 4
        # for memory
        spatial_shapes: torch.Tensor = None,  # bs, num_levels, 2
        valid_ratios: torch.Tensor = None,
        # for text
        memory_text: torch.Tensor = None,
        text_attention_mask: torch.Tensor = None,
        # if `apply_dac` is None, it will default to `self.dac`
        apply_dac: bool | None = None,
        is_instance_prompt=False,
        decoder_extra_kwargs: dict | None = None,
        # ROI memory bank
        obj_roi_memory_feat=None,
        obj_roi_memory_mask=None,
        box_head_trk=None,
    ):
        """Forward pass of the TransformerDecoder."""
        if memory_mask is not None:
            assert self.boxRPB == "none", (
                "inputting a memory_mask in the presence of boxRPB is unexpected/not implemented"
            )

        apply_dac = apply_dac if apply_dac is not None else self.dac
        if apply_dac:
            assert (tgt.shape[0] == self.num_queries) or (
                self.use_instance_query and (tgt.shape[0] == self.instance_query_embed.num_embeddings)
            )

            tgt = tgt.repeat(2, 1, 1)
            # note that we don't tile tgt_mask, since DAC doesn't
            # use self-attention in o2m queries
            if reference_boxes is not None:
                assert (reference_boxes.shape[0] == self.num_queries) or (
                    self.use_instance_query and (reference_boxes.shape[0] == self.instance_query_embed.num_embeddings)
                )
                reference_boxes = reference_boxes.repeat(2, 1, 1)

        bs = tgt.shape[1]
        intermediate = []
        intermediate_presence_logits = []
        presence_feats = None

        if self.box_refine:
            if reference_boxes is None:
                # In this case, we're in a one-stage model, so we generate the reference boxes
                reference_boxes = self.reference_points.weight.unsqueeze(1)
                reference_boxes = reference_boxes.repeat(2, bs, 1) if apply_dac else reference_boxes.repeat(1, bs, 1)
                reference_boxes = reference_boxes.sigmoid()
            intermediate_ref_boxes = [reference_boxes]
        else:
            reference_boxes = None
            intermediate_ref_boxes = None

        output = tgt
        presence_out = None
        if self.presence_token is not None and is_instance_prompt is False:
            # expand to batch dim
            presence_out = self.presence_token.weight[None].expand(1, bs, -1)

        box_head = self.bbox_embed
        if is_instance_prompt and self.instance_bbox_embed is not None:
            box_head = self.instance_bbox_embed

        out_norm = self.norm
        if is_instance_prompt and self.instance_norm is not None:
            out_norm = self.instance_norm

        for layer_idx, layer in enumerate(self.layers):
            reference_points_input = (
                reference_boxes[:, :, None] * torch.cat([valid_ratios, valid_ratios], -1)[None, :]
            )  # nq, bs, nlevel, 4

            query_sine_embed = gen_sineembed_for_position(
                reference_points_input[:, :, 0, :], self.d_model
            )  # nq, bs, d_model*2

            # conditional query
            query_pos = self.ref_point_head(query_sine_embed)  # nq, bs, d_model

            if self.boxRPB != "none" and reference_boxes is not None:
                assert spatial_shapes.shape[0] == 1, "only single scale support implemented"
                memory_mask = self._get_rpb_matrix(
                    reference_boxes,
                    (spatial_shapes[0, 0], spatial_shapes[0, 1]),
                )
                memory_mask = memory_mask.flatten(0, 1)  # (bs*n_heads, nq, H*W)
            if self.training:
                assert self.use_act_checkpoint, "Activation checkpointing not enabled in the decoder"
            output, presence_out = layer(
                tgt=output,
                tgt_query_pos=query_pos,
                memory_text=memory_text,
                text_attention_mask=text_attention_mask,
                memory=memory,
                memory_key_padding_mask=memory_key_padding_mask,
                memory_pos=pos,
                self_attn_mask=tgt_mask,
                cross_attn_mask=memory_mask,
                dac=apply_dac,
                dac_use_selfatt_ln=self.dac_use_selfatt_ln,
                presence_token=presence_out,
                **(decoder_extra_kwargs or {}),
                # ROI memory bank
                obj_roi_memory_feat=obj_roi_memory_feat,
                obj_roi_memory_mask=obj_roi_memory_mask,
            )

            # iter update
            if self.box_refine:
                reference_before_sigmoid = inverse_sigmoid(reference_boxes)
                if box_head_trk is None:
                    # delta_unsig = self.bbox_embed(output)
                    if not self.use_normed_output_consistently:
                        delta_unsig = box_head(output)
                    else:
                        delta_unsig = box_head(out_norm(output))
                else:
                    # box_head_trk use a separate box head for tracking queries
                    Q_det = decoder_extra_kwargs["Q_det"]
                    assert output.size(0) >= Q_det
                    delta_unsig_det = self.bbox_embed(output[:Q_det])
                    delta_unsig_trk = box_head_trk(output[Q_det:])
                    delta_unsig = torch.cat([delta_unsig_det, delta_unsig_trk], dim=0)
                outputs_unsig = delta_unsig + reference_before_sigmoid
                new_reference_points = outputs_unsig.sigmoid()

                reference_boxes = new_reference_points.detach()
                if layer_idx != self.num_layers - 1:
                    intermediate_ref_boxes.append(new_reference_points)
            else:
                raise NotImplementedError("not implemented yet")

            intermediate.append(out_norm(output))
            if self.presence_token is not None and is_instance_prompt is False:
                # norm, mlp head
                intermediate_layer_presence_logits = self.presence_token_head(
                    self.presence_token_out_norm(presence_out)
                ).squeeze(-1)

                # clamp to mitigate numerical issues
                if self.clamp_presence_logits:
                    intermediate_layer_presence_logits.clamp_(
                        min=-self.clamp_presence_logit_max_val,
                        max=self.clamp_presence_logit_max_val,
                    )

                intermediate_presence_logits.append(intermediate_layer_presence_logits)
                presence_feats = presence_out.clone()

        if not self.compiled and self.compile_mode is not None:
            self.forward = torch.compile(self.forward, mode=self.compile_mode, fullgraph=True)
            self.compiled = True

        return (
            torch.stack(intermediate),
            torch.stack(intermediate_ref_boxes),
            (
                torch.stack(intermediate_presence_logits)
                if self.presence_token is not None and is_instance_prompt is False
                else None
            ),
            presence_feats,
        )