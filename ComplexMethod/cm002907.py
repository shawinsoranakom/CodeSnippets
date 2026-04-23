def forward(
        self,
        pixel_values: torch.FloatTensor | None = None,
        vision_embeds: Sam3VisionEncoderOutput | None = None,
        input_ids: torch.LongTensor | None = None,
        attention_mask: torch.Tensor | None = None,
        text_embeds: torch.FloatTensor | None = None,
        input_boxes: torch.FloatTensor | None = None,
        input_boxes_labels: torch.LongTensor | None = None,
        **kwargs: Unpack[TransformersKwargs],
    ) -> Sam3ImageSegmentationOutput:
        r"""
        vision_embeds (`Sam3VisionEncoderOutput`, *optional*):
            Pre-computed vision embeddings. Can be used to easily reuse vision embeddings. If provided, `pixel_values`
            should not be passed. Mutually exclusive with `pixel_values`.
        text_embeds (`torch.FloatTensor` of shape `(batch_size, sequence_length, hidden_size)`, *optional*):
            Pre-computed text embeddings. Can be used to easily reuse text embeddings. If provided, `input_ids`
            should not be passed. Mutually exclusive with `input_ids`.
        input_boxes (`torch.FloatTensor` of shape `(batch_size, num_boxes, 4)`, *optional*):
            Normalized box coordinates in [0, 1] range, in (cx, cy, w, h) format.
        input_boxes_labels (`torch.LongTensor` of shape `(batch_size, num_boxes)`, *optional*):
            Labels for boxes: 1 (positive), 0 (negative).

        Example:

        ```python
        >>> from PIL import Image
        >>> import httpx
        >>> from io import BytesIO
        >>> from transformers import AutoModel, AutoProcessor

        >>> model = AutoModel.from_pretrained("facebook/sam3")
        >>> processor = AutoProcessor.from_pretrained("facebook/sam3")

        >>> url = "https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/transformers/model_doc/sam-car.png"
        >>> with httpx.stream("GET", url) as response:
        ...     image = Image.open(BytesIO(response.read())).convert("RGB")
        >>> text = "car"
        >>> inputs = processor(images=image, text=text, return_tensors="pt")

        >>> # Get segmentation output
        >>> outputs = model(**inputs)
        >>> pred_masks = outputs.pred_masks
        >>> pred_boxes = outputs.pred_boxes
        ```
        """
        if (pixel_values is None) == (vision_embeds is None):
            raise ValueError("You must specify exactly one of pixel_values or vision_embeds")

        if (input_ids is None) == (text_embeds is None):
            raise ValueError("You must specify exactly one of input_ids or text_embeds")

        if pixel_values is not None:
            batch_size = pixel_values.shape[0]
            device = pixel_values.device
        else:
            batch_size = vision_embeds.fpn_hidden_states[0].shape[0]
            device = vision_embeds.fpn_hidden_states[0].device

        if vision_embeds is None:
            vision_outputs = self.vision_encoder(pixel_values, **kwargs)
        else:
            vision_outputs = vision_embeds

        fpn_hidden_states = vision_outputs.fpn_hidden_states[:-1]
        fpn_position_encoding = vision_outputs.fpn_position_encoding[:-1]

        if text_embeds is None:
            text_features = self.get_text_features(
                input_ids=input_ids, attention_mask=attention_mask, return_dict=True
            ).pooler_output
        else:
            text_features = text_embeds

        text_mask = attention_mask.bool() if attention_mask is not None else None
        has_geometry_prompts = input_boxes is not None and input_boxes.numel() > 0

        geometry_prompt_features = None
        geometry_prompt_mask = None

        if has_geometry_prompts:
            if input_boxes is not None and input_boxes.numel() > 0:
                box_embeddings = input_boxes  # [batch_size, num_boxes, 4]
                box_labels = (
                    input_boxes_labels
                    if input_boxes_labels is not None
                    else torch.ones_like(box_embeddings[..., 0], dtype=torch.long)
                )
                box_mask = (
                    (input_boxes_labels != -10)
                    if input_boxes_labels is not None
                    else torch.ones(batch_size, input_boxes.shape[1], dtype=torch.bool, device=device)
                )
                box_labels = torch.where(box_labels == -10, 0, box_labels)
            else:
                box_embeddings = torch.zeros(batch_size, 0, 4, dtype=text_features.dtype, device=device)
                box_labels = torch.zeros(batch_size, 0, dtype=torch.long, device=device)
                box_mask = torch.zeros(batch_size, 0, dtype=torch.bool, device=device)

            geometry_outputs = self.geometry_encoder(
                box_embeddings=box_embeddings,
                box_mask=box_mask,
                box_labels=box_labels,
                img_feats=fpn_hidden_states,
                img_pos_embeds=fpn_position_encoding,
            )

            geometry_prompt_features = geometry_outputs.last_hidden_state
            geometry_prompt_mask = geometry_outputs.attention_mask

        if geometry_prompt_features is not None:
            # Repeat text_features for all geometry prompts
            if text_features.shape[0] == 1 and geometry_prompt_features.shape[0] > 1:
                text_features = text_features.repeat(geometry_prompt_features.shape[0], 1, 1)
            combined_prompt_features = torch.cat([text_features, geometry_prompt_features], dim=1)
            if text_mask is not None and text_mask.shape[0] == 1 and geometry_prompt_mask.shape[0] > 1:
                text_mask = text_mask.repeat(geometry_prompt_mask.shape[0], 1)

            if text_mask is not None and geometry_prompt_mask is not None:
                combined_prompt_mask = torch.cat([text_mask, geometry_prompt_mask], dim=1)
            elif text_mask is not None:
                geo_valid_mask = torch.ones(
                    batch_size, geometry_prompt_features.shape[1], dtype=torch.bool, device=device
                )
                combined_prompt_mask = torch.cat([text_mask, geo_valid_mask], dim=1)
            elif geometry_prompt_mask is not None:
                text_valid_mask = torch.ones(batch_size, text_features.shape[1], dtype=torch.bool, device=device)
                combined_prompt_mask = torch.cat([text_valid_mask, geometry_prompt_mask], dim=1)
            else:
                combined_prompt_mask = None
        else:
            combined_prompt_features = text_features
            combined_prompt_mask = text_mask

        encoder_outputs = self.detr_encoder(
            vision_features=[fpn_hidden_states[-1]],
            text_features=combined_prompt_features,
            vision_pos_embeds=[fpn_position_encoding[-1]],
            text_mask=combined_prompt_mask,
            **kwargs,
        )

        decoder_outputs = self.detr_decoder(
            vision_features=encoder_outputs.last_hidden_state,
            text_features=encoder_outputs.text_features,
            vision_pos_encoding=encoder_outputs.pos_embeds_flattened,
            text_mask=combined_prompt_mask,
            spatial_shapes=encoder_outputs.spatial_shapes,
            **kwargs,
        )

        # Refine boxes from decoder
        all_box_offsets = self.detr_decoder.box_head(decoder_outputs.intermediate_hidden_states)
        reference_boxes_inv_sig = inverse_sigmoid(decoder_outputs.reference_boxes)
        all_pred_boxes_cxcywh = (reference_boxes_inv_sig + all_box_offsets).sigmoid()
        all_pred_boxes = box_cxcywh_to_xyxy(all_pred_boxes_cxcywh)

        all_pred_logits = self.dot_product_scoring(
            decoder_hidden_states=decoder_outputs.intermediate_hidden_states,
            text_features=encoder_outputs.text_features,
            text_mask=combined_prompt_mask,
        ).squeeze(-1)

        pred_logits = all_pred_logits[-1]
        pred_boxes = all_pred_boxes[-1]
        decoder_hidden_states = decoder_outputs.intermediate_hidden_states[-1]
        presence_logits = decoder_outputs.presence_logits[-1]

        mask_outputs = self.mask_decoder(
            decoder_queries=decoder_hidden_states,
            backbone_features=list(fpn_hidden_states),
            encoder_hidden_states=encoder_outputs.last_hidden_state,
            prompt_features=combined_prompt_features,
            prompt_mask=combined_prompt_mask,
            **kwargs,
        )

        return Sam3ImageSegmentationOutput(
            pred_masks=mask_outputs.pred_masks,
            pred_boxes=pred_boxes,
            pred_logits=pred_logits,
            presence_logits=presence_logits,
            semantic_seg=mask_outputs.semantic_seg,
            decoder_hidden_states=decoder_outputs.hidden_states,
            decoder_reference_boxes=decoder_outputs.reference_boxes,
            encoder_hidden_states=encoder_outputs.hidden_states,
            vision_hidden_states=vision_outputs.hidden_states,
            vision_attentions=vision_outputs.attentions,
            detr_encoder_attentions=encoder_outputs.attentions,
            detr_decoder_attentions=decoder_outputs.attentions,
            mask_decoder_attentions=mask_outputs.attentions,
        )