def forward(
        self,
        pixel_values: torch.FloatTensor,
        pixel_mask: torch.LongTensor | None = None,
        decoder_attention_mask: torch.LongTensor | None = None,
        encoder_outputs: torch.FloatTensor | None = None,
        inputs_embeds: torch.FloatTensor | None = None,
        decoder_inputs_embeds: torch.FloatTensor | None = None,
        labels: list[dict] | None = None,
        output_attentions: bool | None = None,
        output_hidden_states: bool | None = None,
        return_dict: bool | None = None,
        **kwargs,
    ) -> tuple[torch.FloatTensor] | DabDetrObjectDetectionOutput:
        r"""
        decoder_attention_mask (`torch.FloatTensor` of shape `(batch_size, num_queries)`, *optional*):
            Not used by default. Can be used to mask object queries.
        inputs_embeds (`torch.FloatTensor` of shape `(batch_size, sequence_length, hidden_size)`, *optional*):
            Optionally, instead of passing the flattened feature map (output of the backbone + projection layer), you
            can choose to directly pass a flattened representation of an image.
        decoder_inputs_embeds (`torch.FloatTensor` of shape `(batch_size, num_queries, hidden_size)`, *optional*):
            Optionally, instead of initializing the queries with a tensor of zeros, you can choose to directly pass an
            embedded representation.
        labels (`list[Dict]` of len `(batch_size,)`, *optional*):
            Labels for computing the bipartite matching loss. List of dicts, each dictionary containing at least the
            following 2 keys: 'class_labels' and 'boxes' (the class labels and bounding boxes of an image in the batch
            respectively). The class labels themselves should be a `torch.LongTensor` of len `(number of bounding boxes
            in the image,)` and the boxes a `torch.FloatTensor` of shape `(number of bounding boxes in the image, 4)`.

        Examples:

        ```python
        >>> from transformers import AutoImageProcessor, AutoModelForObjectDetection
        >>> from PIL import Image
        >>> import httpx
        >>> from io import BytesIO

        >>> url = "http://images.cocodataset.org/val2017/000000039769.jpg"
        >>> with httpx.stream("GET", url) as response:
        ...     image = Image.open(BytesIO(response.read()))

        >>> image_processor = AutoImageProcessor.from_pretrained("IDEA-Research/dab-detr-resnet-50")
        >>> model = AutoModelForObjectDetection.from_pretrained("IDEA-Research/dab-detr-resnet-50")

        >>> inputs = image_processor(images=image, return_tensors="pt")

        >>> with torch.no_grad():
        >>>     outputs = model(**inputs)

        >>> # convert outputs (bounding boxes and class logits) to Pascal VOC format (xmin, ymin, xmax, ymax)
        >>> target_sizes = torch.tensor([(image.height, image.width)])
        >>> results = image_processor.post_process_object_detection(outputs, threshold=0.5, target_sizes=target_sizes)[0]
        >>> for score, label, box in zip(results["scores"], results["labels"], results["boxes"]):
        ...     box = [round(i, 2) for i in box.tolist()]
        ...     print(
        ...         f"Detected {model.config.id2label[label.item()]} with confidence "
        ...         f"{round(score.item(), 3)} at location {box}"
        ...     )
        Detected remote with confidence 0.833 at location [38.31, 72.1, 177.63, 118.45]
        Detected cat with confidence 0.831 at location [9.2, 51.38, 321.13, 469.0]
        Detected cat with confidence 0.804 at location [340.3, 16.85, 642.93, 370.95]
        Detected remote with confidence 0.683 at location [334.48, 73.49, 366.37, 190.01]
        Detected couch with confidence 0.535 at location [0.52, 1.19, 640.35, 475.1]
        ```"""
        output_attentions = output_attentions if output_attentions is not None else self.config.output_attentions
        output_hidden_states = (
            output_hidden_states if output_hidden_states is not None else self.config.output_hidden_states
        )
        return_dict = return_dict if return_dict is not None else self.config.return_dict

        # First, sent images through DAB_DETR base model to obtain encoder + decoder outputs
        model_outputs = self.model(
            pixel_values,
            pixel_mask=pixel_mask,
            decoder_attention_mask=decoder_attention_mask,
            encoder_outputs=encoder_outputs,
            inputs_embeds=inputs_embeds,
            decoder_inputs_embeds=decoder_inputs_embeds,
            output_attentions=output_attentions,
            output_hidden_states=output_hidden_states,
            return_dict=return_dict,
        )

        reference_points = model_outputs.reference_points if return_dict else model_outputs[-1]
        intermediate_hidden_states = model_outputs.intermediate_hidden_states if return_dict else model_outputs[-2]

        # class logits + predicted bounding boxes
        logits = self.class_embed(intermediate_hidden_states[-1])

        reference_before_sigmoid = inverse_sigmoid(reference_points)
        bbox_with_refinement = self.bbox_predictor(intermediate_hidden_states)
        bbox_with_refinement[..., : self.query_dim] += reference_before_sigmoid
        outputs_coord = bbox_with_refinement.sigmoid()

        pred_boxes = outputs_coord[-1]

        loss, loss_dict, auxiliary_outputs = None, None, None
        if labels is not None:
            outputs_class = None
            if self.config.auxiliary_loss:
                outputs_class = self.class_embed(intermediate_hidden_states)
            loss, loss_dict, auxiliary_outputs = self.loss_function(
                logits, labels, self.device, pred_boxes, self.config, outputs_class, outputs_coord
            )

        if not return_dict:
            if auxiliary_outputs is not None:
                output = (logits, pred_boxes) + auxiliary_outputs + model_outputs
            else:
                output = (logits, pred_boxes) + model_outputs
            # Since DabDetrObjectDetectionOutput doesn't have reference points + intermedieate_hidden_states we cut down.
            return ((loss, loss_dict) + output) if loss is not None else output[:-2]

        return DabDetrObjectDetectionOutput(
            loss=loss,
            loss_dict=loss_dict,
            logits=logits,
            pred_boxes=pred_boxes,
            auxiliary_outputs=auxiliary_outputs,
            last_hidden_state=model_outputs.last_hidden_state,
            decoder_hidden_states=model_outputs.decoder_hidden_states if output_hidden_states else None,
            decoder_attentions=model_outputs.decoder_attentions if output_attentions else None,
            cross_attentions=model_outputs.cross_attentions if output_attentions else None,
            encoder_last_hidden_state=model_outputs.encoder_last_hidden_state if output_hidden_states else None,
            encoder_hidden_states=model_outputs.encoder_hidden_states if output_hidden_states else None,
            encoder_attentions=model_outputs.encoder_attentions if output_attentions else None,
        )