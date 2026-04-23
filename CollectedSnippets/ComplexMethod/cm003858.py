def forward(
        self,
        pixel_values: torch.FloatTensor,
        input_ids: torch.LongTensor,
        token_type_ids: torch.LongTensor | None = None,
        attention_mask: torch.LongTensor | None = None,
        pixel_mask: torch.BoolTensor | None = None,
        encoder_outputs: GroundingDinoEncoderOutput | tuple | None = None,
        output_attentions: bool | None = None,
        output_hidden_states: bool | None = None,
        return_dict: bool | None = None,
        labels: list[dict[str, torch.LongTensor | torch.FloatTensor]] | None = None,
        **kwargs,
    ):
        r"""
        input_ids (`torch.LongTensor` of shape `(batch_size, text_sequence_length)`):
            Indices of input sequence tokens in the vocabulary. Padding will be ignored by default should you provide
            it.

            Indices can be obtained using [`AutoTokenizer`]. See [`BertTokenizer.__call__`] for details.
        token_type_ids (`torch.LongTensor` of shape `(batch_size, text_sequence_length)`, *optional*):
            Segment token indices to indicate first and second portions of the inputs. Indices are selected in `[0,
            1]`: 0 corresponds to a `sentence A` token, 1 corresponds to a `sentence B` token

            [What are token type IDs?](../glossary#token-type-ids)
        labels (`list[Dict]` of len `(batch_size,)`, *optional*):
            Labels for computing the bipartite matching loss. List of dicts, each dictionary containing at least the
            following 2 keys: 'class_labels' and 'boxes' (the class labels and bounding boxes of an image in the batch
            respectively). The class labels themselves should be a `torch.LongTensor` of len `(number of bounding boxes
            in the image,)` and the boxes a `torch.FloatTensor` of shape `(number of bounding boxes in the image, 4)`.

        Examples:

        ```python
        >>> import httpx
        >>> from io import BytesIO

        >>> import torch
        >>> from PIL import Image
        >>> from transformers import AutoProcessor, AutoModelForZeroShotObjectDetection

        >>> model_id = "IDEA-Research/grounding-dino-tiny"
        >>> device = "cuda"

        >>> processor = AutoProcessor.from_pretrained(model_id)
        >>> model = AutoModelForZeroShotObjectDetection.from_pretrained(model_id).to(device)

        >>> url = "http://images.cocodataset.org/val2017/000000039769.jpg"
        >>> with httpx.stream("GET", url) as response:
        ...     image = Image.open(BytesIO(response.read()))
        >>> # Check for cats and remote controls
        >>> text_labels = [["a cat", "a remote control"]]

        >>> inputs = processor(images=image, text=text_labels, return_tensors="pt").to(device)
        >>> with torch.no_grad():
        ...     outputs = model(**inputs)

        >>> results = processor.post_process_grounded_object_detection(
        ...     outputs,
        ...     threshold=0.4,
        ...     text_threshold=0.3,
        ...     target_sizes=[(image.height, image.width)]
        ... )
        >>> # Retrieve the first image result
        >>> result = results[0]
        >>> for box, score, text_label in zip(result["boxes"], result["scores"], result["text_labels"]):
        ...     box = [round(x, 2) for x in box.tolist()]
        ...     print(f"Detected {text_label} with confidence {round(score.item(), 3)} at location {box}")
        Detected a cat with confidence 0.479 at location [344.7, 23.11, 637.18, 374.28]
        Detected a cat with confidence 0.438 at location [12.27, 51.91, 316.86, 472.44]
        Detected a remote control with confidence 0.478 at location [38.57, 70.0, 176.78, 118.18]
        ```"""
        return_dict = return_dict if return_dict is not None else self.config.return_dict

        if attention_mask is None:
            attention_mask = torch.ones_like(input_ids)

        # First, sent images through Grounding DINO base model to obtain encoder + decoder outputs
        outputs = self.model(
            pixel_values=pixel_values,
            input_ids=input_ids,
            token_type_ids=token_type_ids,
            attention_mask=attention_mask,
            pixel_mask=pixel_mask,
            encoder_outputs=encoder_outputs,
            output_attentions=output_attentions,
            output_hidden_states=output_hidden_states,
            return_dict=return_dict,
        )

        idx = 5 + (1 if output_attentions else 0) + (1 if output_hidden_states else 0)
        enc_text_hidden_state = outputs.encoder_last_hidden_state_text if return_dict else outputs[idx]
        hidden_states = outputs.intermediate_hidden_states if return_dict else outputs[2]
        init_reference_points = outputs.init_reference_points if return_dict else outputs[1]
        inter_references_points = outputs.intermediate_reference_points if return_dict else outputs[3]

        # class logits + predicted bounding boxes
        outputs_classes = []
        outputs_coords = []

        # hidden_states are of shape (batch_size, num_stages, height, width)
        # predict class and bounding box deltas for each stage
        num_levels = hidden_states.shape[1]
        for level in range(num_levels):
            if level == 0:
                reference = init_reference_points
            else:
                reference = inter_references_points[:, level - 1]
            reference = torch.special.logit(reference, eps=1e-5)
            outputs_class = self.class_embed[level](
                vision_hidden_state=hidden_states[:, level],
                text_hidden_state=enc_text_hidden_state,
                text_token_mask=attention_mask.bool(),
            )
            delta_bbox = self.bbox_embed[level](hidden_states[:, level])

            reference_coordinates = reference.shape[-1]
            if reference_coordinates == 4:
                outputs_coord_logits = delta_bbox + reference
            elif reference_coordinates == 2:
                delta_bbox[..., :2] += reference
                outputs_coord_logits = delta_bbox
            else:
                raise ValueError(f"reference.shape[-1] should be 4 or 2, but got {reference.shape[-1]}")
            outputs_coord = outputs_coord_logits.sigmoid()
            outputs_classes.append(outputs_class)
            outputs_coords.append(outputs_coord)
        outputs_class = torch.stack(outputs_classes)
        outputs_coord = torch.stack(outputs_coords)

        logits = outputs_class[-1]
        pred_boxes = outputs_coord[-1]

        loss, loss_dict, auxiliary_outputs = None, None, None
        if labels is not None:
            label_maps = build_label_maps(logits, input_ids)
            text_mask = build_text_mask(logits, attention_mask)
            loss, loss_dict, auxiliary_outputs = self.loss_function(
                logits,
                labels,
                self.device,
                pred_boxes,
                self.config,
                label_maps,
                text_mask,
                outputs_class=outputs_class,
                outputs_coord=outputs_coord,
                encoder_logits=outputs[-2],
                encoder_pred_boxes=outputs[-1],
            )

        if not return_dict:
            auxiliary_outputs = auxiliary_outputs if auxiliary_outputs is not None else []
            output = [loss, loss_dict, logits, pred_boxes, *auxiliary_outputs, *outputs, input_ids]
            output = tuple(out for out in output if out is not None)
            return output

        dict_outputs = GroundingDinoObjectDetectionOutput(
            loss=loss,
            loss_dict=loss_dict,
            logits=logits,
            pred_boxes=pred_boxes,
            last_hidden_state=outputs.last_hidden_state,
            auxiliary_outputs=auxiliary_outputs,
            decoder_hidden_states=outputs.decoder_hidden_states,
            decoder_attentions=outputs.decoder_attentions,
            encoder_last_hidden_state_vision=outputs.encoder_last_hidden_state_vision,
            encoder_last_hidden_state_text=outputs.encoder_last_hidden_state_text,
            encoder_vision_hidden_states=outputs.encoder_vision_hidden_states,
            encoder_text_hidden_states=outputs.encoder_text_hidden_states,
            encoder_attentions=outputs.encoder_attentions,
            intermediate_hidden_states=outputs.intermediate_hidden_states,
            intermediate_reference_points=outputs.intermediate_reference_points,
            init_reference_points=outputs.init_reference_points,
            enc_outputs_class=outputs.enc_outputs_class,
            enc_outputs_coord_logits=outputs.enc_outputs_coord_logits,
            encoder_logits=outputs.encoder_logits,
            encoder_pred_boxes=outputs.encoder_pred_boxes,
            input_ids=input_ids,
        )

        return dict_outputs