def forward(
        self,
        pixel_values: torch.FloatTensor = None,
        pixel_mask: torch.LongTensor | None = None,
        **kwargs: Unpack[TransformersKwargs],
    ) -> LwDetrModelOutput:
        r"""
        Examples:

        ```python
        >>> from transformers import AutoImageProcessor, DeformableDetrModel
        >>> from PIL import Image
        >>> import httpx
        >>> from io import BytesIO

        >>> url = "http://images.cocodataset.org/val2017/000000039769.jpg"
        >>> with httpx.stream("GET", url) as response:
        ...     image = Image.open(BytesIO(response.read()))

        >>> image_processor = AutoImageProcessor.from_pretrained("AnnaZhang/lwdetr_small_60e_coco")
        >>> model = DeformableDetrModel.from_pretrained("AnnaZhang/lwdetr_small_60e_coco")

        >>> inputs = image_processor(images=image, return_tensors="pt")

        >>> outputs = model(**inputs)

        >>> last_hidden_states = outputs.last_hidden_state
        >>> list(last_hidden_states.shape)
        [1, 300, 256]
        ```"""
        batch_size, num_channels, height, width = pixel_values.shape
        device = pixel_values.device

        if pixel_mask is None:
            pixel_mask = torch.ones(((batch_size, height, width)), dtype=torch.long, device=device)

        # Extract multi-scale feature maps of same resolution `config.d_model` (cf Figure 4 in paper)
        # First, sent pixel_values + pixel_mask through Backbone to obtain the features
        # which is a list of tuples
        features = self.backbone(pixel_values, pixel_mask)

        # Then, apply 1x1 convolution to reduce the channel dimension to d_model (256 by default)
        sources = []
        masks = []
        for level, (source, mask) in enumerate(features):
            sources.append(source)
            masks.append(mask)
            if mask is None:
                raise ValueError("No attention mask was provided")

        if self.training:
            reference_points = self.reference_point_embed.weight
            query_feat = self.query_feat.weight
        else:
            # only use one group in inference
            reference_points = self.reference_point_embed.weight[: self.num_queries]
            query_feat = self.query_feat.weight[: self.num_queries]

        # Prepare encoder inputs (by flattening)
        source_flatten = []
        mask_flatten = []
        spatial_shapes_list = []
        for source, mask in zip(sources, masks):
            batch_size, num_channels, height, width = source.shape
            spatial_shape = (height, width)
            spatial_shapes_list.append(spatial_shape)
            source = source.flatten(2).transpose(1, 2)
            mask = mask.flatten(1)
            source_flatten.append(source)
            mask_flatten.append(mask)
        source_flatten = torch.cat(source_flatten, 1)
        mask_flatten = torch.cat(mask_flatten, 1)
        spatial_shapes = torch.as_tensor(spatial_shapes_list, dtype=torch.long, device=source_flatten.device)
        level_start_index = torch.cat((spatial_shapes.new_zeros((1,)), spatial_shapes.prod(1).cumsum(0)[:-1]))
        valid_ratios = torch.stack([self.get_valid_ratio(m, dtype=source_flatten.dtype) for m in masks], 1)

        target = query_feat.unsqueeze(0).expand(batch_size, -1, -1)
        reference_points = reference_points.unsqueeze(0).expand(batch_size, -1, -1)

        object_query_embedding, output_proposals, invalid_mask = self.gen_encoder_output_proposals(
            source_flatten, ~mask_flatten, spatial_shapes_list
        )

        group_detr = self.group_detr if self.training else 1
        topk = self.num_queries
        topk_coords_logits = []
        topk_coords_logits_undetach = []
        object_query_undetach = []

        for group_id in range(group_detr):
            group_object_query = self.enc_output[group_id](object_query_embedding)
            group_object_query = self.enc_output_norm[group_id](group_object_query)

            group_enc_outputs_class = self.enc_out_class_embed[group_id](group_object_query)
            group_enc_outputs_class = group_enc_outputs_class.masked_fill(invalid_mask, float("-inf"))
            group_delta_bbox = self.enc_out_bbox_embed[group_id](group_object_query)
            group_enc_outputs_coord = refine_bboxes(output_proposals, group_delta_bbox)

            group_topk_proposals = torch.topk(group_enc_outputs_class.max(-1)[0], topk, dim=1)[1]
            group_topk_coords_logits_undetach = torch.gather(
                group_enc_outputs_coord,
                1,
                group_topk_proposals.unsqueeze(-1).repeat(1, 1, 4),
            )
            group_topk_coords_logits = group_topk_coords_logits_undetach.detach()
            group_object_query_undetach = torch.gather(
                group_object_query, 1, group_topk_proposals.unsqueeze(-1).repeat(1, 1, self.config.d_model)
            )

            topk_coords_logits.append(group_topk_coords_logits)
            topk_coords_logits_undetach.append(group_topk_coords_logits_undetach)
            object_query_undetach.append(group_object_query_undetach)

        topk_coords_logits = torch.cat(topk_coords_logits, 1)
        topk_coords_logits_undetach = torch.cat(topk_coords_logits_undetach, 1)
        object_query_undetach = torch.cat(object_query_undetach, 1)

        enc_outputs_class = object_query_undetach
        enc_outputs_coord_logits = topk_coords_logits_undetach

        reference_points = refine_bboxes(topk_coords_logits, reference_points)

        init_reference_points = reference_points
        decoder_outputs = self.decoder(
            inputs_embeds=target,
            reference_points=reference_points,
            spatial_shapes=spatial_shapes,
            spatial_shapes_list=spatial_shapes_list,
            level_start_index=level_start_index,
            valid_ratios=valid_ratios,
            encoder_hidden_states=source_flatten,
            encoder_attention_mask=mask_flatten,
            **kwargs,
        )

        return LwDetrModelOutput(
            init_reference_points=init_reference_points,
            last_hidden_state=decoder_outputs.last_hidden_state,
            intermediate_hidden_states=decoder_outputs.intermediate_hidden_states,
            intermediate_reference_points=decoder_outputs.intermediate_reference_points,
            enc_outputs_class=enc_outputs_class,
            enc_outputs_coord_logits=enc_outputs_coord_logits,
            hidden_states=decoder_outputs.hidden_states,
            attentions=decoder_outputs.attentions,
            cross_attentions=decoder_outputs.cross_attentions,
        )