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
    ) -> tuple | SegGptEncoderOutput:
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
        >>> from transformers import SegGptImageProcessor, SegGptModel
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
        >>> model = SegGptModel.from_pretrained(checkpoint)
        >>> image_processor = SegGptImageProcessor.from_pretrained(checkpoint)

        >>> inputs = image_processor(images=image_input, prompt_images=image_prompt, prompt_masks=mask_prompt, return_tensors="pt")

        >>> outputs = model(**inputs)
        >>> list(outputs.last_hidden_state.shape)
        [1, 56, 28, 1024]
        ```
        """
        output_attentions = output_attentions if output_attentions is not None else self.config.output_attentions
        output_hidden_states = (
            output_hidden_states if output_hidden_states is not None else self.config.output_hidden_states
        )
        return_dict = return_dict if return_dict is not None else self.config.return_dict
        feature_ensemble = feature_ensemble if feature_ensemble is not None else False

        expected_dtype = self.embeddings.patch_embeddings.projection.weight.dtype
        pixel_values = pixel_values.to(expected_dtype)
        prompt_pixel_values = prompt_pixel_values.to(expected_dtype)

        # Prepare inputs
        pixel_values = torch.cat((prompt_pixel_values, pixel_values), dim=2)
        prompt_pixel_values = (
            torch.cat((prompt_masks, prompt_masks), dim=2)
            if labels is None
            else torch.cat((prompt_masks, labels), dim=2)
        )

        if bool_masked_pos is None and labels is not None:
            logger.warning_once(
                "Labels were provided, but bool_masked_pos were not. It will be set to default value. If you're training the model, make sure to provide a bool_masked_pos."
            )

        # We concat on height axis so SegGPT can handle as a single image, hence we need to mask the portion
        # of the mask prompt pixels that will be destinated to the prediction as they don't add any information.
        # This is only the case for inference. In training, the model concat of prompt mask and label is masked
        # and reconstructed together (In-Context Painting).
        if bool_masked_pos is None:
            num_patches = self.embeddings.patch_embeddings.num_patches
            bool_masked_pos_zeros = torch.zeros(num_patches // 2, dtype=torch.bool, device=pixel_values.device)
            bool_masked_pos_ones = torch.ones(
                num_patches - num_patches // 2, dtype=torch.bool, device=pixel_values.device
            )
            bool_masked_pos = torch.cat([bool_masked_pos_zeros, bool_masked_pos_ones])
            bool_masked_pos = bool_masked_pos.unsqueeze(0)

        embedding_output = self.embeddings(
            pixel_values, prompt_pixel_values, embedding_type=embedding_type, bool_masked_pos=bool_masked_pos
        )

        encoder_outputs = self.encoder(
            embedding_output,
            feature_ensemble=feature_ensemble,
            output_attentions=output_attentions,
            output_hidden_states=output_hidden_states,
            return_dict=return_dict,
        )

        return encoder_outputs