def forward(
        self,
        pixel_values: Tensor,
        task_inputs: Tensor,
        text_inputs: Tensor | None = None,
        mask_labels: list[Tensor] | None = None,
        class_labels: list[Tensor] | None = None,
        pixel_mask: Tensor | None = None,
        output_auxiliary_logits: bool | None = None,
        output_hidden_states: bool | None = None,
        output_attentions: bool | None = None,
        return_dict: bool | None = None,
        **kwargs,
    ) -> OneFormerForUniversalSegmentationOutput:
        r"""
        task_inputs (`torch.FloatTensor` of shape `(batch_size, sequence_length)`):
            Task inputs. Task inputs can be obtained using [`AutoImageProcessor`]. See [`OneFormerProcessor.__call__`]
            for details.
        text_inputs (`list[torch.Tensor]`, *optional*):
            Tensor of shape `(num_queries, sequence_length)` to be fed to a model
        mask_labels (`list[torch.Tensor]`, *optional*):
            List of mask labels of shape `(num_labels, height, width)` to be fed to a model
        class_labels (`list[torch.LongTensor]`, *optional*):
            list of target class labels of shape `(num_labels, height, width)` to be fed to a model. They identify the
            labels of `mask_labels`, e.g. the label of `mask_labels[i][j]` if `class_labels[i][j]`.
        output_auxiliary_logits (`bool`, *optional*):
            Whether or not to output auxiliary logits.

        Example:

        Universal segmentation example:

        ```python
        >>> from transformers import OneFormerProcessor, OneFormerForUniversalSegmentation
        >>> from PIL import Image
        >>> import httpx
        >>> from io import BytesIO
        >>> import torch

        >>> # load OneFormer fine-tuned on ADE20k for universal segmentation
        >>> processor = OneFormerProcessor.from_pretrained("shi-labs/oneformer_ade20k_swin_tiny")
        >>> model = OneFormerForUniversalSegmentation.from_pretrained("shi-labs/oneformer_ade20k_swin_tiny")

        >>> url = (
        ...     "https://huggingface.co/datasets/hf-internal-testing/fixtures_ade20k/resolve/main/ADE_val_00000001.jpg"
        ... )
        >>> with httpx.stream("GET", url) as response:
        ...     image = Image.open(BytesIO(response.read()))

        >>> # Semantic Segmentation
        >>> inputs = processor(image, ["semantic"], return_tensors="pt")

        >>> with torch.no_grad():
        ...     outputs = model(**inputs)
        >>> # model predicts class_queries_logits of shape `(batch_size, num_queries)`
        >>> # and masks_queries_logits of shape `(batch_size, num_queries, height, width)`
        >>> class_queries_logits = outputs.class_queries_logits
        >>> masks_queries_logits = outputs.masks_queries_logits

        >>> # you can pass them to processor for semantic postprocessing
        >>> predicted_semantic_map = processor.post_process_semantic_segmentation(
        ...     outputs, target_sizes=[(image.height, image.width)]
        ... )[0]
        >>> f"👉 Semantic Predictions Shape: {list(predicted_semantic_map.shape)}"
        '👉 Semantic Predictions Shape: [512, 683]'

        >>> # Instance Segmentation
        >>> inputs = processor(image, ["instance"], return_tensors="pt")

        >>> with torch.no_grad():
        ...     outputs = model(**inputs)
        >>> # model predicts class_queries_logits of shape `(batch_size, num_queries)`
        >>> # and masks_queries_logits of shape `(batch_size, num_queries, height, width)`
        >>> class_queries_logits = outputs.class_queries_logits
        >>> masks_queries_logits = outputs.masks_queries_logits

        >>> # you can pass them to processor for instance postprocessing
        >>> predicted_instance_map = processor.post_process_instance_segmentation(
        ...     outputs, target_sizes=[(image.height, image.width)]
        ... )[0]["segmentation"]
        >>> f"👉 Instance Predictions Shape: {list(predicted_instance_map.shape)}"
        '👉 Instance Predictions Shape: [512, 683]'

        >>> # Panoptic Segmentation
        >>> inputs = processor(image, ["panoptic"], return_tensors="pt")

        >>> with torch.no_grad():
        ...     outputs = model(**inputs)
        >>> # model predicts class_queries_logits of shape `(batch_size, num_queries)`
        >>> # and masks_queries_logits of shape `(batch_size, num_queries, height, width)`
        >>> class_queries_logits = outputs.class_queries_logits
        >>> masks_queries_logits = outputs.masks_queries_logits

        >>> # you can pass them to processor for panoptic postprocessing
        >>> predicted_panoptic_map = processor.post_process_panoptic_segmentation(
        ...     outputs, target_sizes=[(image.height, image.width)]
        ... )[0]["segmentation"]
        >>> f"👉 Panoptic Predictions Shape: {list(predicted_panoptic_map.shape)}"
        '👉 Panoptic Predictions Shape: [512, 683]'
        ```
        """

        output_attentions = output_attentions if output_attentions is not None else self.config.output_attentions
        output_hidden_states = (
            output_hidden_states if output_hidden_states is not None else self.config.output_hidden_states
        )
        return_dict = return_dict if return_dict is not None else self.config.return_dict

        outputs = self.model(
            pixel_values=pixel_values,
            task_inputs=task_inputs,
            text_inputs=text_inputs,
            pixel_mask=pixel_mask,
            output_hidden_states=output_hidden_states or self.config.use_auxiliary_loss,
            output_attentions=output_attentions,
            return_dict=True,
        )

        loss, loss_dict, auxiliary_predictions = None, None, None

        class_queries_logits = outputs.transformer_decoder_class_predictions
        masks_queries_logits = outputs.transformer_decoder_mask_predictions
        contrastive_queries_logits = outputs.transformer_decoder_contrastive_queries
        auxiliary_predictions = outputs.transformer_decoder_auxiliary_predictions
        text_queries = outputs.text_queries

        if mask_labels is not None and class_labels is not None:
            loss_dict: dict[str, Tensor] = self.get_loss_dict(
                masks_queries_logits=masks_queries_logits,
                class_queries_logits=class_queries_logits,
                contrastive_queries_logits=contrastive_queries_logits,
                mask_labels=mask_labels,
                class_labels=class_labels,
                text_queries=text_queries,
                auxiliary_predictions=auxiliary_predictions,
                calculate_contrastive_loss=self.config.contrastive_temperature is not None,
            )
            loss = self.get_loss(loss_dict)

        output_auxiliary_logits = (
            self.config.output_auxiliary_logits if output_auxiliary_logits is None else output_auxiliary_logits
        )
        if not output_auxiliary_logits:
            auxiliary_predictions = None

        output = OneFormerForUniversalSegmentationOutput(
            class_queries_logits=class_queries_logits,
            masks_queries_logits=masks_queries_logits,
            auxiliary_predictions=auxiliary_predictions,
            loss=loss,
            **outputs,
        )

        if not return_dict:
            output = tuple(v for v in output.values())
            if loss is not None:
                output = (loss) + output
        return output