def forward(
        self,
        pixel_values: Tensor,
        mask_labels: list[Tensor] | None = None,
        class_labels: list[Tensor] | None = None,
        pixel_mask: Tensor | None = None,
        output_auxiliary_logits: bool | None = None,
        output_hidden_states: bool | None = None,
        output_attentions: bool | None = None,
        return_dict: bool | None = None,
        **kwargs,
    ) -> MaskFormerForInstanceSegmentationOutput:
        r"""
        mask_labels (`list[torch.Tensor]`, *optional*):
            List of mask labels of shape `(num_labels, height, width)` to be fed to a model
        class_labels (`list[torch.LongTensor]`, *optional*):
            list of target class labels of shape `(num_labels, height, width)` to be fed to a model. They identify the
            labels of `mask_labels`, e.g. the label of `mask_labels[i][j]` if `class_labels[i][j]`.
        output_auxiliary_logits (`bool`, *optional*):
            Whether or not to output auxiliary logits.

        Examples:

        Semantic segmentation example:

        ```python
        >>> from transformers import AutoImageProcessor, MaskFormerForInstanceSegmentation
        >>> from PIL import Image
        >>> import httpx
        >>> from io import BytesIO

        >>> # load MaskFormer fine-tuned on ADE20k semantic segmentation
        >>> image_processor = AutoImageProcessor.from_pretrained("facebook/maskformer-swin-base-ade")
        >>> model = MaskFormerForInstanceSegmentation.from_pretrained("facebook/maskformer-swin-base-ade")

        >>> url = (
        ...     "https://huggingface.co/datasets/hf-internal-testing/fixtures_ade20k/resolve/main/ADE_val_00000001.jpg"
        ... )
        >>> with httpx.stream("GET", url) as response:
        ...     image = Image.open(BytesIO(response.read()))
        >>> inputs = image_processor(images=image, return_tensors="pt")

        >>> outputs = model(**inputs)
        >>> # model predicts class_queries_logits of shape `(batch_size, num_queries)`
        >>> # and masks_queries_logits of shape `(batch_size, num_queries, height, width)`
        >>> class_queries_logits = outputs.class_queries_logits
        >>> masks_queries_logits = outputs.masks_queries_logits

        >>> # you can pass them to image_processor for postprocessing
        >>> predicted_semantic_map = image_processor.post_process_semantic_segmentation(
        ...     outputs, target_sizes=[(image.height, image.width)]
        ... )[0]

        >>> # we refer to the demo notebooks for visualization (see "Resources" section in the MaskFormer docs)
        >>> list(predicted_semantic_map.shape)
        [512, 683]
        ```

        Panoptic segmentation example:

        ```python
        >>> from transformers import AutoImageProcessor, MaskFormerForInstanceSegmentation
        >>> from PIL import Image
        >>> import httpx
        >>> from io import BytesIO

        >>> # load MaskFormer fine-tuned on COCO panoptic segmentation
        >>> image_processor = AutoImageProcessor.from_pretrained("facebook/maskformer-swin-base-coco")
        >>> model = MaskFormerForInstanceSegmentation.from_pretrained("facebook/maskformer-swin-base-coco")

        >>> url = "http://images.cocodataset.org/val2017/000000039769.jpg"
        >>> with httpx.stream("GET", url) as response:
        ...     image = Image.open(BytesIO(response.read()))
        >>> inputs = image_processor(images=image, return_tensors="pt")

        >>> outputs = model(**inputs)
        >>> # model predicts class_queries_logits of shape `(batch_size, num_queries)`
        >>> # and masks_queries_logits of shape `(batch_size, num_queries, height, width)`
        >>> class_queries_logits = outputs.class_queries_logits
        >>> masks_queries_logits = outputs.masks_queries_logits

        >>> # you can pass them to image_processor for postprocessing
        >>> result = image_processor.post_process_panoptic_segmentation(outputs, target_sizes=[(image.height, image.width)])[0]

        >>> # we refer to the demo notebooks for visualization (see "Resources" section in the MaskFormer docs)
        >>> predicted_panoptic_map = result["segmentation"]
        >>> list(predicted_panoptic_map.shape)
        [480, 640]
        ```
        """

        output_attentions = output_attentions if output_attentions is not None else self.config.output_attentions
        output_hidden_states = (
            output_hidden_states if output_hidden_states is not None else self.config.output_hidden_states
        )
        return_dict = return_dict if return_dict is not None else self.config.return_dict

        raw_outputs = self.model(
            pixel_values,
            pixel_mask,
            output_hidden_states=output_hidden_states or self.config.use_auxiliary_loss,
            return_dict=return_dict,
            output_attentions=output_attentions,
        )
        # We need to have raw_outputs optionally be returned as a dict to use torch.compile. For backwards
        # compatibility we convert to a dataclass for the rest of the model logic
        outputs = MaskFormerModelOutput(
            encoder_last_hidden_state=raw_outputs[0],
            pixel_decoder_last_hidden_state=raw_outputs[1],
            transformer_decoder_last_hidden_state=raw_outputs[2],
            encoder_hidden_states=raw_outputs[3] if output_hidden_states else None,
            pixel_decoder_hidden_states=raw_outputs[4] if output_hidden_states else None,
            transformer_decoder_hidden_states=raw_outputs[5] if output_hidden_states else None,
            hidden_states=raw_outputs[6] if output_hidden_states else None,
            attentions=raw_outputs[-1] if output_attentions else None,
        )

        loss, loss_dict, auxiliary_logits = None, None, None

        class_queries_logits, masks_queries_logits, auxiliary_logits = self.get_logits(outputs)

        if mask_labels is not None and class_labels is not None:
            loss_dict: dict[str, Tensor] = self.get_loss_dict(
                masks_queries_logits, class_queries_logits, mask_labels, class_labels, auxiliary_logits
            )
            loss = self.get_loss(loss_dict)

        output_auxiliary_logits = (
            self.config.output_auxiliary_logits if output_auxiliary_logits is None else output_auxiliary_logits
        )
        if not output_auxiliary_logits:
            auxiliary_logits = None

        if not return_dict:
            output = tuple(
                v
                for v in (loss, class_queries_logits, masks_queries_logits, auxiliary_logits, *outputs.values())
                if v is not None
            )
            return output

        return MaskFormerForInstanceSegmentationOutput(
            loss=loss,
            **outputs,
            class_queries_logits=class_queries_logits,
            masks_queries_logits=masks_queries_logits,
            auxiliary_logits=auxiliary_logits,
        )