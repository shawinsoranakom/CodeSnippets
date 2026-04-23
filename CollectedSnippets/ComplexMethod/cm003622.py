def forward(
        self,
        pixel_values: torch.FloatTensor,
        labels: torch.LongTensor | None = None,
        output_attentions: bool | None = None,
        output_hidden_states: bool | list[int] | None = None,
        return_dict: bool | None = None,
        **kwargs,
    ) -> ImageClassifierOutput | tuple[Tensor, ...]:
        r"""
        labels (`torch.LongTensor` of shape `(batch_size,)`, *optional*):
            Labels for computing the image classification/regression loss. Indices should be in `[0, ...,
            config.num_labels - 1]`. If `config.num_labels == 1` a regression loss is computed (Mean-Square loss), If
            `config.num_labels > 1` a classification loss is computed (Cross-Entropy).
        output_attentions (`bool`, *optional*):
            Whether or not to return the attentions tensors of all attention layers. Not compatible with timm wrapped models.
        output_hidden_states (`bool`, *optional*):
            Whether or not to return the hidden states of all layers. Not compatible with timm wrapped models.
        return_dict (`bool`, *optional*):
            Whether or not to return a [`~utils.ModelOutput`] instead of a plain tuple.
            **kwargs:
            Additional keyword arguments passed along to the `timm` model forward.

        Examples:
        ```python
        >>> import torch
        >>> from PIL import Image
        >>> from urllib.request import urlopen
        >>> from transformers import AutoModelForImageClassification, AutoImageProcessor

        >>> # Load image
        >>> image = Image.open(urlopen(
        ...     'https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/beignets-task-guide.png'
        ... ))

        >>> # Load model and image processor
        >>> checkpoint = "timm/resnet50.a1_in1k"
        >>> image_processor = AutoImageProcessor.from_pretrained(checkpoint)
        >>> model = AutoModelForImageClassification.from_pretrained(checkpoint).eval()

        >>> # Preprocess image
        >>> inputs = image_processor(image)

        >>> # Forward pass
        >>> with torch.no_grad():
        ...     logits = model(**inputs).logits

        >>> # Get top 5 predictions
        >>> top5_probabilities, top5_class_indices = torch.topk(logits.softmax(dim=1) * 100, k=5)
        ```
        """
        return_dict = return_dict if return_dict is not None else self.config.return_dict
        output_hidden_states = (
            output_hidden_states if output_hidden_states is not None else self.config.output_hidden_states
        )
        output_attentions = output_attentions if output_attentions is not None else self.config.output_attentions

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

        if output_hidden_states:
            # to enable hidden states selection
            if isinstance(output_hidden_states, (list, tuple)):
                kwargs["indices"] = output_hidden_states
            last_hidden_state, hidden_states = self.timm_model.forward_intermediates(pixel_values, **kwargs)
            logits = self.timm_model.forward_head(last_hidden_state)
        else:
            logits = self.timm_model(pixel_values, **kwargs)
            hidden_states = None

        loss = None
        if labels is not None:
            loss = self.loss_function(labels, logits, self.config)

        if not return_dict:
            outputs = (loss, logits, hidden_states)
            outputs = tuple(output for output in outputs if output is not None)
            return outputs

        return ImageClassifierOutput(
            loss=loss,
            logits=logits,
            hidden_states=hidden_states,
        )