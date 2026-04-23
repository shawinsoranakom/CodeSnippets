def forward(
        self,
        pixel_values: torch.Tensor,
        prompt_pixel_values: torch.Tensor,
        prompt_masks: torch.Tensor,
        bool_masked_pos: torch.BoolTensor | None = None,
        feature_ensemble: bool | None = None,
        embedding_type: str | None = None,
        labels: torch.FloatTensor | None = None,
        output_attentions: bool | None = None,
        output_hidden_states: bool | None = None,
        return_dict: bool | None = None,
        **kwargs,
    ) -> tuple | SegGptImageSegmentationOutput:
        r"""
        prompt_pixel_values (`torch.FloatTensor` of shape `(batch_size, num_channels, height, width)`):
            Prompt pixel values. Prompt pixel values can be obtained using [`AutoImageProcessor`]. See
            [`SegGptImageProcessor.__call__`] for details.
        prompt_masks (`torch.FloatTensor` of shape `(batch_size, num_channels, height, width)`):
            Prompt mask. Prompt mask can be obtained using [`AutoImageProcessor`]. See [`SegGptImageProcessor.__call__`] for
            details.
        bool_masked_pos (`torch.BoolTensor` of shape `(batch_size, num_patches)`, *optional*):
            Boolean masked positions. Indicates which patches are masked (1) and which aren't (0).
        feature_ensemble (`bool`, *optional*):
            Boolean indicating whether to use feature ensemble or not. If `True`, the model will use feature ensemble
            if we have at least two prompts. If `False`, the model will not use feature ensemble. This argument should
            be considered when doing few-shot inference on an input image i.e. more than one prompt for the same image.
        embedding_type (`str`, *optional*):
            Embedding type. Indicates whether the prompt is a semantic or instance embedding. Can be either
            instance or semantic.
        labels (`torch.FloatTensor` of shape `(batch_size, num_channels, height, width)`, `optional`):
            Ground truth mask for input images.

        Examples:

        ```python
        >>> from transformers import SegGptImageProcessor, SegGptForImageSegmentation
        >>> from PIL import Image
        >>> import httpx
        >>> from io import BytesIO

        >>> image_input_url = "https://raw.githubusercontent.com/baaivision/Painter/main/SegGPT/SegGPT_inference/examples/hmbb_2.jpg"
        >>> image_prompt_url = "https://raw.githubusercontent.com/baaivision/Painter/main/SegGPT/SegGPT_inference/examples/hmbb_1.jpg"
        >>> mask_prompt_url = "https://raw.githubusercontent.com/baaivision/Painter/main/SegGPT/SegGPT_inference/examples/hmbb_1_target.png"

        >>> with httpx.stream("GET", image_input_url) as response:
        ...     image_input = Image.open(BytesIO(response.read()))

        >>> with httpx.stream("GET", image_prompt_url) as response:
        ...     image_prompt = Image.open(BytesIO(response.read()))

        >>> with httpx.stream("GET", mask_prompt_url) as response:
        ...     mask_prompt = Image.open(BytesIO(response.read())).convert("L")

        >>> checkpoint = "BAAI/seggpt-vit-large"
        >>> model = SegGptForImageSegmentation.from_pretrained(checkpoint)
        >>> image_processor = SegGptImageProcessor.from_pretrained(checkpoint)

        >>> inputs = image_processor(images=image_input, prompt_images=image_prompt, prompt_masks=mask_prompt, return_tensors="pt")
        >>> outputs = model(**inputs)
        >>> result = image_processor.post_process_semantic_segmentation(outputs, target_sizes=[(image_input.height, image_input.width)])[0]
        >>> print(list(result.shape))
        [170, 297]
        ```
        """
        output_attentions = output_attentions if output_attentions is not None else self.config.output_attentions
        output_hidden_states = (
            output_hidden_states if output_hidden_states is not None else self.config.output_hidden_states
        )
        return_dict = return_dict if return_dict is not None else self.config.return_dict

        if bool_masked_pos is None:
            num_patches = self.model.embeddings.patch_embeddings.num_patches
            bool_masked_pos_zeros = torch.zeros(num_patches // 2, dtype=torch.bool, device=pixel_values.device)
            bool_masked_pos_ones = torch.ones(
                num_patches - num_patches // 2, dtype=torch.bool, device=pixel_values.device
            )
            bool_masked_pos = torch.cat([bool_masked_pos_zeros, bool_masked_pos_ones])
            bool_masked_pos = bool_masked_pos.unsqueeze(0)

        outputs = self.model(
            pixel_values=pixel_values,
            prompt_pixel_values=prompt_pixel_values,
            prompt_masks=prompt_masks,
            bool_masked_pos=bool_masked_pos,
            feature_ensemble=feature_ensemble,
            embedding_type=embedding_type,
            labels=labels,
            output_attentions=output_attentions,
            output_hidden_states=output_hidden_states,
            return_dict=return_dict,
        )

        intermediate_hidden_states = outputs.intermediate_hidden_states if return_dict else outputs[-1]
        intermediate_hidden_states = torch.cat(intermediate_hidden_states, dim=-1)
        pred_masks = self.decoder(intermediate_hidden_states)

        loss = None
        if labels is not None:
            loss_fn = SegGptLoss(self.config)
            loss = loss_fn(prompt_masks, pred_masks, labels, bool_masked_pos)

        if not return_dict:
            output = (pred_masks,)
            if output_hidden_states:
                output = output + (outputs[1],)

            if output_attentions:
                idx = 2 if output_hidden_states else 1
                output = output + (outputs[idx],)

            if loss is not None:
                output = (loss,) + output
            return output

        return SegGptImageSegmentationOutput(
            loss=loss,
            pred_masks=pred_masks,
            hidden_states=outputs.hidden_states,
            attentions=outputs.attentions,
        )