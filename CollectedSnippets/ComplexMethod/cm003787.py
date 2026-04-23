def forward(
        self,
        pixel_values: Tensor,
        task_inputs: Tensor,
        text_inputs: Tensor | None = None,
        pixel_mask: Tensor | None = None,
        output_hidden_states: bool | None = None,
        output_attentions: bool | None = None,
        return_dict: bool | None = None,
        **kwargs,
    ) -> OneFormerModelOutput:
        r"""
        task_inputs (`torch.FloatTensor` of shape `(batch_size, sequence_length)`):
            Task inputs. Task inputs can be obtained using [`AutoImageProcessor`]. See [`OneFormerProcessor.__call__`]
            for details.
        text_inputs (`list[torch.Tensor]`, *optional*):
            Tensor of shape `(num_queries, sequence_length)` to be fed to a model

        Example:

        ```python
        >>> import torch
        >>> from PIL import Image
        >>> import httpx
        >>> from io import BytesIO
        >>> from transformers import OneFormerProcessor, OneFormerModel

        >>> # download texting image
        >>> url = "http://images.cocodataset.org/val2017/000000039769.jpg"
        >>> with httpx.stream("GET", url) as response:
        ...     image = Image.open(BytesIO(response.read()))

        >>> # load processor for preprocessing the inputs
        >>> processor = OneFormerProcessor.from_pretrained("shi-labs/oneformer_ade20k_swin_tiny")
        >>> model = OneFormerModel.from_pretrained("shi-labs/oneformer_ade20k_swin_tiny")
        >>> inputs = processor(image, ["semantic"], return_tensors="pt")

        >>> with torch.no_grad():
        ...     outputs = model(**inputs)

        >>> mask_predictions = outputs.transformer_decoder_mask_predictions
        >>> class_predictions = outputs.transformer_decoder_class_predictions

        >>> f"👉 Mask Predictions Shape: {list(mask_predictions.shape)}, Class Predictions Shape: {list(class_predictions.shape)}"
        '👉 Mask Predictions Shape: [1, 150, 128, 171], Class Predictions Shape: [1, 150, 151]'
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

        pixel_level_module_output = self.pixel_level_module(pixel_values, output_hidden_states)

        multi_scale_features = pixel_level_module_output.decoder_features
        mask_features = pixel_level_module_output.decoder_last_feature

        task_token = self.task_encoder(task_inputs.to(self.dtype))

        if self.is_training:
            text_queries = self.text_mapper(text_inputs)
        else:
            text_queries = None

        transformer_module_output = self.transformer_module(
            multi_scale_features=multi_scale_features,
            mask_features=mask_features,
            task_token=task_token,
            output_attentions=output_attentions,
        )

        queries = transformer_module_output.object_queries

        encoder_hidden_states = None
        pixel_decoder_hidden_states = None
        transformer_decoder_hidden_states = None

        if output_hidden_states:
            encoder_hidden_states = pixel_level_module_output.encoder_features
            pixel_decoder_hidden_states = (pixel_level_module_output.decoder_last_feature,)
            for f in pixel_level_module_output.decoder_features:
                pixel_decoder_hidden_states += (f,)
            transformer_decoder_hidden_states = transformer_module_output.auxiliary_predictions

        output = OneFormerModelOutput(
            encoder_hidden_states=encoder_hidden_states,
            pixel_decoder_hidden_states=pixel_decoder_hidden_states,
            transformer_decoder_hidden_states=transformer_decoder_hidden_states,
            transformer_decoder_object_queries=queries,
            transformer_decoder_contrastive_queries=transformer_module_output.contrastive_logits,
            transformer_decoder_mask_predictions=transformer_module_output.prediction_masks,
            transformer_decoder_class_predictions=transformer_module_output.prediction_class,
            transformer_decoder_auxiliary_predictions=transformer_module_output.auxiliary_predictions,
            text_queries=text_queries,
            task_token=task_token,
            attentions=transformer_module_output.attentions,
        )

        if not return_dict:
            output = tuple(v for v in output.values())

        return output