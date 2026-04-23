def forward(
        self,
        pixel_values: torch.FloatTensor,
        labels: torch.LongTensor | None = None,
        **kwargs: Unpack[TransformersKwargs],
    ) -> DepthEstimatorOutput:
        r"""
        labels (`torch.LongTensor` of shape `(batch_size, height, width)`, *optional*):
            Ground truth depth estimation maps for computing the loss.

        Examples:
        ```python
        >>> from transformers import AutoImageProcessor, DPTForDepthEstimation
        >>> import torch
        >>> import numpy as np
        >>> from PIL import Image
        >>> import httpx
        >>> from io import BytesIO

        >>> url = "http://images.cocodataset.org/val2017/000000039769.jpg"
        >>> with httpx.stream("GET", url) as response:
        ...     image = Image.open(BytesIO(response.read()))

        >>> image_processor = AutoImageProcessor.from_pretrained("Intel/dpt-large")
        >>> model = DPTForDepthEstimation.from_pretrained("Intel/dpt-large")

        >>> # prepare image for the model
        >>> inputs = image_processor(images=image, return_tensors="pt")

        >>> with torch.no_grad():
        ...     outputs = model(**inputs)

        >>> # interpolate to original size
        >>> post_processed_output = image_processor.post_process_depth_estimation(
        ...     outputs,
        ...     target_sizes=[(image.height, image.width)],
        ... )

        >>> # visualize the prediction
        >>> predicted_depth = post_processed_output[0]["predicted_depth"]
        >>> depth = predicted_depth * 255 / predicted_depth.max()
        >>> depth = depth.detach().cpu().numpy()
        >>> depth = Image.fromarray(depth.astype("uint8"))
        ```"""
        loss = None
        if labels is not None:
            raise NotImplementedError("Training is not implemented yet")

        # Internally the model always needs to output hidden states, we control the output
        # per user request on the final output
        user_requested_hidden_states = kwargs.get("output_hidden_states") or getattr(
            self.config, "output_hidden_states", False
        )
        kwargs["output_hidden_states"] = True

        if self.backbone is not None:
            outputs = self.backbone.forward_with_filtered_kwargs(pixel_values, **kwargs)
            hidden_states = outputs.feature_maps
        else:
            outputs = self.dpt(pixel_values, **kwargs)
            hidden_states = outputs.hidden_states
            # only keep certain features based on config.backbone_out_indices
            # note that the hidden_states also include the initial embeddings
            if not self.config.is_hybrid:
                hidden_states = [
                    feature for idx, feature in enumerate(hidden_states[1:]) if idx in self.config.backbone_out_indices
                ]
            else:
                backbone_hidden_states = outputs.intermediate_activations
                backbone_hidden_states.extend(
                    feature
                    for idx, feature in enumerate(hidden_states[1:])
                    if idx in self.config.backbone_out_indices[2:]
                )
                hidden_states = backbone_hidden_states

        patch_height, patch_width = None, None
        if self.config.backbone_config is not None and self.config.is_hybrid is False:
            _, _, height, width = pixel_values.shape
            patch_size = self.config.backbone_config.patch_size
            patch_height = height // patch_size
            patch_width = width // patch_size

        hidden_states = self.neck(hidden_states, patch_height, patch_width)
        predicted_depth = self.head(hidden_states)

        return DepthEstimatorOutput(
            loss=loss,
            predicted_depth=predicted_depth,
            hidden_states=outputs.hidden_states if user_requested_hidden_states else None,
            attentions=outputs.attentions,
        )