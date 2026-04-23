def forward(
        self,
        pixel_values: torch.FloatTensor,
        classes_input_ids: torch.LongTensor,
        classes_attention_mask: torch.LongTensor,
        tasks_input_ids: torch.LongTensor,
        tasks_attention_mask: torch.LongTensor,
        classes_structure: torch.LongTensor,
        labels: torch.LongTensor | None = None,
        output_attentions: bool | None = None,
        output_hidden_states: bool | None = None,
        return_dict: bool | None = None,
        **kwargs,
    ) -> tuple[torch.FloatTensor] | OmDetTurboObjectDetectionOutput:
        r"""
        classes_input_ids (`torch.LongTensor` of shape `(total_classes (>= batch_size), sequence_length)`):
            Indices of input classes sequence tokens in the vocabulary of the language model.
            Several classes can be provided for each tasks, thus the tokenized classes are flattened
            and the structure of the classes is provided in the `classes_structure` argument.

            Indices can be obtained using [`OmDetTurboProcessor`]. See [`OmDetTurboProcessor.__call__`] for
            details.

            [What are input IDs?](../glossary#input-ids)
        classes_attention_mask (`torch.BoolTensor` of shape `(total_classes (>= batch_size), num_classes, sequence_length)`):
            Attention mask for the classes. This is a binary mask that indicates which tokens should be attended to,
            and which should not.
        tasks_input_ids (`torch.LongTensor` of shape `(batch_size, sequence_length)`):
            Indices of input tasks sequence tokens in the vocabulary of the language model.

            Indices can be obtained using [`OmDetTurboProcessor`]. See [`OmDetTurboProcessor.__call__`] for
            details.

            [What are input IDs?](../glossary#input-ids)
        tasks_attention_mask (`torch.BoolTensor` of shape `(batch_size, sequence_length)`):
            Attention mask for the tasks. This is a binary mask that indicates which tokens should be attended to,
            and which should not.
        classes_structure (torch.LongTensor of shape `(batch_size)`):
            Structure of the classes. This tensor indicates the number of classes for each task.

        Examples:

        ```python
        >>> import httpx
        >>> from io import BytesIO
        >>> from PIL import Image

        >>> from transformers import AutoProcessor, OmDetTurboForObjectDetection

        >>> processor = AutoProcessor.from_pretrained("omlab/omdet-turbo-swin-tiny-hf")
        >>> model = OmDetTurboForObjectDetection.from_pretrained("omlab/omdet-turbo-swin-tiny-hf")

        >>> url = "http://images.cocodataset.org/val2017/000000039769.jpg"
        >>> with httpx.stream("GET", url) as response:
        ...     image = Image.open(BytesIO(response.read()))
        >>> classes = ["cat", "remote"]
        >>> task = "Detect {}.".format(", ".join(classes))
        >>> inputs = processor(image, text=classes, task=task, return_tensors="pt")

        >>> outputs = model(**inputs)

        >>> # convert outputs (bounding boxes and class logits)
        >>> results = processor.post_process_grounded_object_detection(
        ...     outputs,
        ...     classes=classes,
        ...     target_sizes=[image.size[::-1]],
        ...     score_threshold=0.3,
        ...     nms_threshold=0.3,
        >>> )[0]
        >>> for score, class_name, box in zip(results["scores"], results["classes"], results["boxes"]):
        ...     box = [round(i, 1) for i in box.tolist()]
        ...     print(
        ...         f"Detected {class_name} with confidence "
        ...         f"{round(score.item(), 2)} at location {box}"
        ...     )
        Detected remote with confidence 0.76 at location [39.9, 71.3, 176.5, 117.9]
        Detected cat with confidence 0.72 at location [345.1, 22.5, 639.7, 371.9]
        Detected cat with confidence 0.65 at location [12.7, 53.8, 315.5, 475.3]
        Detected remote with confidence 0.57 at location [333.4, 75.6, 370.7, 187.0]
        ```"""
        if labels is not None:
            raise NotImplementedError("Training is not implemented yet")

        output_attentions = output_attentions if output_attentions is not None else self.config.output_attentions
        output_hidden_states = (
            output_hidden_states if output_hidden_states is not None else self.config.output_hidden_states
        )
        return_dict = return_dict if return_dict is not None else self.config.return_dict

        loss = None
        image_features = self.vision_backbone(pixel_values)
        encoder_outputs = self.encoder(
            image_features,
            output_attentions=output_attentions,
            output_hidden_states=output_hidden_states,
            return_dict=return_dict,
        )
        class_features, task_features, task_mask = self.get_language_embedding(
            classes_input_ids,
            classes_attention_mask,
            tasks_input_ids,
            tasks_attention_mask,
            classes_structure,
        )
        encoder_extracted_states = encoder_outputs.extracted_states if return_dict else encoder_outputs[-1]
        decoder_outputs = self.decoder(
            encoder_extracted_states,
            class_features,
            task_features,
            task_mask,
            output_attentions=output_attentions,
            output_hidden_states=output_hidden_states,
            return_dict=return_dict,
        )

        if not return_dict:
            return tuple(
                output
                for output in [
                    loss,
                    decoder_outputs[3][-1],
                    decoder_outputs[4][-1],
                    decoder_outputs[7],
                    decoder_outputs[8],
                    decoder_outputs[5],
                    decoder_outputs[6],
                    encoder_outputs[-1],
                    decoder_outputs[1],
                    decoder_outputs[2],
                    encoder_outputs[1],
                    encoder_outputs[2],
                    classes_structure,
                ]
                if output is not None
            )

        return OmDetTurboObjectDetectionOutput(
            loss=loss,
            decoder_coord_logits=decoder_outputs.decoder_coords[-1],
            decoder_class_logits=decoder_outputs.decoder_classes[-1],
            init_reference_points=decoder_outputs.init_reference_points,
            intermediate_reference_points=decoder_outputs.intermediate_reference_points,
            encoder_coord_logits=decoder_outputs.encoder_coord_logits,
            encoder_class_logits=decoder_outputs.encoder_class_logits,
            encoder_extracted_states=encoder_outputs.extracted_states,
            decoder_hidden_states=decoder_outputs.hidden_states,
            decoder_attentions=decoder_outputs.attentions,
            encoder_hidden_states=encoder_outputs.hidden_states,
            encoder_attentions=encoder_outputs.attentions,
            classes_structure=classes_structure,
        )