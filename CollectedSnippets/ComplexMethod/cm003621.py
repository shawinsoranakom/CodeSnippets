def forward(
        self,
        pixel_values: torch.FloatTensor,
        output_attentions: bool | None = None,
        output_hidden_states: bool | list[int] | None = None,
        return_dict: bool | None = None,
        do_pooling: bool | None = None,
        use_cache: bool | None = None,
        **kwargs,
    ) -> TimmWrapperModelOutput | tuple[Tensor, ...]:
        r"""
        output_attentions (`bool`, *optional*):
            Whether or not to return the attentions tensors of all attention layers. Not compatible with timm wrapped models.
        output_hidden_states (`bool`, *optional*):
            Whether or not to return the hidden states of all layers. Not compatible with timm wrapped models.
        do_pooling (`bool`, *optional*):
            Whether to do pooling for the last_hidden_state in `TimmWrapperModel` or not. If `None` is passed, the
            `do_pooling` value from the config is used.

        Examples:
        ```python
        >>> import torch
        >>> from PIL import Image
        >>> from urllib.request import urlopen
        >>> from transformers import AutoModel, AutoImageProcessor

        >>> # Load image
        >>> image = Image.open(urlopen(
        ...     'https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/beignets-task-guide.png'
        ... ))

        >>> # Load model and image processor
        >>> checkpoint = "timm/resnet50.a1_in1k"
        >>> image_processor = AutoImageProcessor.from_pretrained(checkpoint)
        >>> model = AutoModel.from_pretrained(checkpoint).eval()

        >>> # Preprocess image
        >>> inputs = image_processor(image)

        >>> # Forward pass
        >>> with torch.no_grad():
        ...     outputs = model(**inputs)

        >>> # Get pooled output
        >>> pooled_output = outputs.pooler_output

        >>> # Get last hidden state
        >>> last_hidden_state = outputs.last_hidden_state
        ```
        """
        return_dict = return_dict if return_dict is not None else self.config.return_dict
        output_hidden_states = (
            output_hidden_states if output_hidden_states is not None else self.config.output_hidden_states
        )
        output_attentions = output_attentions if output_attentions is not None else self.config.output_attentions
        do_pooling = do_pooling if do_pooling is not None else self.config.do_pooling

        if output_attentions:
            raise ValueError("Cannot set `output_attentions` for timm models.")

        if output_hidden_states and not hasattr(self.timm_model, "forward_intermediates"):
            raise ValueError(
                "The 'output_hidden_states' option cannot be set for this timm model. "
                "To enable this feature, the 'forward_intermediates' method must be implemented "
                "in the timm model (available in timm versions > 1.*). Please consider using a "
                "different architecture or updating the timm package to a compatible version."
            )

        pixel_values = pixel_values.to(self.device, self.dtype)

        if self.features_only:
            last_hidden_state = self.timm_model.forward(pixel_values, **kwargs)
            hidden_states = last_hidden_state if output_hidden_states else None
            pooler_output = None
        else:
            if output_hidden_states:
                # to enable hidden states selection
                if isinstance(output_hidden_states, (list, tuple)):
                    kwargs["indices"] = output_hidden_states
                last_hidden_state, hidden_states = self.timm_model.forward_intermediates(pixel_values, **kwargs)
            else:
                last_hidden_state = self.timm_model.forward_features(pixel_values, **kwargs)
                hidden_states = None

            if do_pooling:
                # classification head is not created, applying pooling only
                pooler_output = self.timm_model.forward_head(last_hidden_state)
            else:
                pooler_output = None

        if not return_dict:
            outputs = (last_hidden_state, pooler_output, hidden_states)
            outputs = tuple(output for output in outputs if output is not None)
            return outputs

        return TimmWrapperModelOutput(
            last_hidden_state=last_hidden_state,
            pooler_output=pooler_output,
            hidden_states=hidden_states,
        )