def forward(
        self,
        pixel_values: Tensor,
        mask_labels: list[Tensor] | None = None,
        class_labels: list[Tensor] | None = None,
        pixel_mask: Tensor | None = None,
        output_hidden_states: bool | None = None,
        output_auxiliary_logits: bool | None = None,
        output_attentions: bool | None = None,
        return_dict: bool | None = None,
        **kwargs,
    ) -> Mask2FormerForUniversalSegmentationOutput:
        r"""
        mask_labels (`list[torch.Tensor]`, *optional*):
            List of mask labels of shape `(num_labels, height, width)` to be fed to a model
        class_labels (`list[torch.LongTensor]`, *optional*):
            list of target class labels of shape `(num_labels, height, width)` to be fed to a model. They identify the
            labels of `mask_labels`, e.g. the label of `mask_labels[i][j]` if `class_labels[i][j]`.
        output_auxiliary_logits (`bool`, *optional*):
            Whether or not to output auxiliary logits.

        Examples:

        Instance segmentation example:

        ```python
        >>> from transformers import AutoImageProcessor, Mask2FormerForUniversalSegmentation
        >>> from PIL import Image
        >>> import httpx
        >>> from io import BytesIO
        >>> import torch

        >>> # Load Mask2Former trained on COCO instance segmentation dataset
        >>> image_processor = AutoImageProcessor.from_pretrained("facebook/mask2former-swin-small-coco-instance")
        >>> model = Mask2FormerForUniversalSegmentation.from_pretrained(
        ...     "facebook/mask2former-swin-small-coco-instance"
        ... )

        >>> url = "http://images.cocodataset.org/val2017/000000039769.jpg"
        >>> with httpx.stream("GET", url) as response:
        ...     image = Image.open(BytesIO(response.read()))
        >>> inputs = image_processor(image, return_tensors="pt")

        >>> with torch.no_grad():
        ...     outputs = model(**inputs)

        >>> # Model predicts class_queries_logits of shape `(batch_size, num_queries)`
        >>> # and masks_queries_logits of shape `(batch_size, num_queries, height, width)`
        >>> class_queries_logits = outputs.class_queries_logits
        >>> masks_queries_logits = outputs.masks_queries_logits

        >>> # Perform post-processing to get instance segmentation map
        >>> pred_instance_map = image_processor.post_process_instance_segmentation(
        ...     outputs, target_sizes=[(image.height, image.width)]
        ... )[0]
        >>> print(pred_instance_map.shape)
        torch.Size([480, 640])
        ```

        Semantic segmentation example:
        ```python
        >>> from transformers import AutoImageProcessor, Mask2FormerForUniversalSegmentation
        >>> from PIL import Image
        >>> import httpx
        >>> from io import BytesIO
        >>> import torch

        >>> # Load Mask2Former trained on ADE20k semantic segmentation dataset
        >>> image_processor = AutoImageProcessor.from_pretrained("facebook/mask2former-swin-small-ade-semantic")
        >>> model = Mask2FormerForUniversalSegmentation.from_pretrained("facebook/mask2former-swin-small-ade-semantic")

        >>> url = (
        ...     "https://huggingface.co/datasets/hf-internal-testing/fixtures_ade20k/resolve/main/ADE_val_00000001.jpg"
        ... )
        >>> with httpx.stream("GET", url) as response:
        ...     image = Image.open(BytesIO(response.read()))
        >>> inputs = image_processor(image, return_tensors="pt")

        >>> with torch.no_grad():
        ...     outputs = model(**inputs)

        >>> # Model predicts class_queries_logits of shape `(batch_size, num_queries)`
        >>> # and masks_queries_logits of shape `(batch_size, num_queries, height, width)`
        >>> class_queries_logits = outputs.class_queries_logits
        >>> masks_queries_logits = outputs.masks_queries_logits

        >>> # Perform post-processing to get semantic segmentation map
        >>> pred_semantic_map = image_processor.post_process_semantic_segmentation(
        ...     outputs, target_sizes=[(image.height, image.width)]
        ... )[0]
        >>> print(pred_semantic_map.shape)
        torch.Size([512, 683])
        ```

        Panoptic segmentation example:

        ```python
        >>> from transformers import AutoImageProcessor, Mask2FormerForUniversalSegmentation
        >>> from PIL import Image
        >>> import httpx
        >>> from io import BytesIO
        >>> import torch

        >>> # Load Mask2Former trained on CityScapes panoptic segmentation dataset
        >>> image_processor = AutoImageProcessor.from_pretrained("facebook/mask2former-swin-small-cityscapes-panoptic")
        >>> model = Mask2FormerForUniversalSegmentation.from_pretrained(
        ...     "facebook/mask2former-swin-small-cityscapes-panoptic"
        ... )

        >>> url = "https://cdn-media.huggingface.co/Inference-API/Sample-results-on-the-Cityscapes-dataset-The-above-images-show-how-our-method-can-handle.png"
        >>> with httpx.stream("GET", url) as response:
        ...     image = Image.open(BytesIO(response.read()))
        >>> inputs = image_processor(image, return_tensors="pt")

        >>> with torch.no_grad():
        ...     outputs = model(**inputs)

        >>> # Model predicts class_queries_logits of shape `(batch_size, num_queries)`
        >>> # and masks_queries_logits of shape `(batch_size, num_queries, height, width)`
        >>> class_queries_logits = outputs.class_queries_logits
        >>> masks_queries_logits = outputs.masks_queries_logits

        >>> # Perform post-processing to get panoptic segmentation map
        >>> pred_panoptic_map = image_processor.post_process_panoptic_segmentation(
        ...     outputs, target_sizes=[(image.height, image.width)]
        ... )[0]["segmentation"]
        >>> print(pred_panoptic_map.shape)
        torch.Size([338, 676])
        ```
        """
        output_attentions = output_attentions if output_attentions is not None else self.config.output_attentions
        output_hidden_states = (
            output_hidden_states if output_hidden_states is not None else self.config.output_hidden_states
        )
        return_dict = return_dict if return_dict is not None else self.config.return_dict

        outputs = self.model(
            pixel_values=pixel_values,
            pixel_mask=pixel_mask,
            output_hidden_states=output_hidden_states or self.config.use_auxiliary_loss,
            output_attentions=output_attentions,
            return_dict=True,
        )

        loss, loss_dict, auxiliary_logits = None, None, None
        class_queries_logits = ()

        for decoder_output in outputs.transformer_decoder_intermediate_states:
            class_prediction = self.class_predictor(decoder_output.transpose(0, 1))
            class_queries_logits += (class_prediction,)

        masks_queries_logits = outputs.masks_queries_logits

        auxiliary_logits = self.get_auxiliary_logits(class_queries_logits, masks_queries_logits)

        if mask_labels is not None and class_labels is not None:
            loss_dict = self.get_loss_dict(
                masks_queries_logits=masks_queries_logits[-1],
                class_queries_logits=class_queries_logits[-1],
                mask_labels=mask_labels,
                class_labels=class_labels,
                auxiliary_predictions=auxiliary_logits,
            )
            loss = self.get_loss(loss_dict)

        encoder_hidden_states = None
        pixel_decoder_hidden_states = None
        transformer_decoder_hidden_states = None

        if output_hidden_states:
            encoder_hidden_states = outputs.encoder_hidden_states
            pixel_decoder_hidden_states = outputs.pixel_decoder_hidden_states
            transformer_decoder_hidden_states = outputs.transformer_decoder_hidden_states

        output_auxiliary_logits = (
            self.config.output_auxiliary_logits if output_auxiliary_logits is None else output_auxiliary_logits
        )
        if not output_auxiliary_logits:
            auxiliary_logits = None

        output = Mask2FormerForUniversalSegmentationOutput(
            loss=loss,
            class_queries_logits=class_queries_logits[-1],
            masks_queries_logits=masks_queries_logits[-1],
            auxiliary_logits=auxiliary_logits,
            encoder_last_hidden_state=outputs.encoder_last_hidden_state,
            pixel_decoder_last_hidden_state=outputs.pixel_decoder_last_hidden_state,
            transformer_decoder_last_hidden_state=outputs.transformer_decoder_last_hidden_state,
            encoder_hidden_states=encoder_hidden_states,
            pixel_decoder_hidden_states=pixel_decoder_hidden_states,
            transformer_decoder_hidden_states=transformer_decoder_hidden_states,
            attentions=outputs.attentions,
        )

        if not return_dict:
            output = tuple(v for v in output.values() if v is not None)
            if loss is not None:
                output = (loss) + output
        return output