def forward(
        self,
        pixel_values: Tensor,
        pixel_mask: Tensor | None = None,
        output_hidden_states: bool | None = None,
        output_attentions: bool | None = None,
        return_dict: bool | None = None,
        **kwargs,
    ) -> MaskFormerModelOutput:
        r"""
        Examples:

        ```python
        >>> from transformers import AutoImageProcessor, MaskFormerModel
        >>> from PIL import Image
        >>> import httpx
        >>> from io import BytesIO

        >>> # load MaskFormer fine-tuned on ADE20k semantic segmentation
        >>> image_processor = AutoImageProcessor.from_pretrained("facebook/maskformer-swin-base-ade")
        >>> model = MaskFormerModel.from_pretrained("facebook/maskformer-swin-base-ade")

        >>> url = "http://images.cocodataset.org/val2017/000000039769.jpg"
        >>> with httpx.stream("GET", url) as response:
        ...     image = Image.open(BytesIO(response.read()))

        >>> inputs = image_processor(image, return_tensors="pt")

        >>> # forward pass
        >>> outputs = model(**inputs)

        >>> # the decoder of MaskFormer outputs hidden states of shape (batch_size, num_queries, hidden_size)
        >>> transformer_decoder_last_hidden_state = outputs.transformer_decoder_last_hidden_state
        >>> list(transformer_decoder_last_hidden_state.shape)
        [1, 100, 256]
        ```"""

        if pixel_values is None:
            raise ValueError("You have to specify pixel_values")

        output_attentions = output_attentions if output_attentions is not None else self.config.output_attentions
        output_hidden_states = (
            output_hidden_states if output_hidden_states is not None else self.config.output_hidden_states
        )
        return_dict = return_dict if return_dict is not None else self.config.return_dict

        batch_size, _, height, width = pixel_values.shape

        if pixel_mask is None:
            pixel_mask = torch.ones((batch_size, height, width), device=pixel_values.device)

        pixel_level_module_output = self.pixel_level_module(
            pixel_values, output_hidden_states, return_dict=return_dict
        )
        image_features = pixel_level_module_output[0]
        pixel_embeddings = pixel_level_module_output[1]

        transformer_module_output = self.transformer_module(image_features, output_hidden_states, output_attentions)
        queries = transformer_module_output.last_hidden_state

        encoder_hidden_states = None
        pixel_decoder_hidden_states = None
        transformer_decoder_hidden_states = None
        hidden_states = None

        if output_hidden_states:
            encoder_hidden_states = pixel_level_module_output[2]
            pixel_decoder_hidden_states = pixel_level_module_output[3]
            transformer_decoder_hidden_states = transformer_module_output[1]
            hidden_states = encoder_hidden_states + pixel_decoder_hidden_states + transformer_decoder_hidden_states

        output = MaskFormerModelOutput(
            encoder_last_hidden_state=image_features,
            pixel_decoder_last_hidden_state=pixel_embeddings,
            transformer_decoder_last_hidden_state=queries,
            encoder_hidden_states=encoder_hidden_states,
            pixel_decoder_hidden_states=pixel_decoder_hidden_states,
            transformer_decoder_hidden_states=transformer_decoder_hidden_states,
            hidden_states=hidden_states,
            attentions=transformer_module_output.attentions,
        )

        if not return_dict:
            output = tuple(v for v in output.values())

        return output