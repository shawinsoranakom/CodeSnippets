def forward(
        self,
        pixel_values: torch.FloatTensor,
        labels: torch.LongTensor | None = None,
        output_attentions: bool | None = None,
        output_hidden_states: bool | None = None,
        return_dict: bool | None = None,
        **kwargs,
    ) -> tuple[torch.Tensor] | DepthProDepthEstimatorOutput:
        r"""
        labels (`torch.LongTensor` of shape `(batch_size, height, width)`, *optional*):
            Ground truth depth estimation maps for computing the loss.

        Examples:

        ```python
        >>> from transformers import AutoImageProcessor, DepthProForDepthEstimation
        >>> import torch
        >>> from PIL import Image
        >>> import httpx
        >>> from io import BytesIO

        >>> url = "http://images.cocodataset.org/val2017/000000039769.jpg"
        >>> with httpx.stream("GET", url) as response:
        ...     image = Image.open(BytesIO(response.read()))

        >>> checkpoint = "apple/DepthPro-hf"
        >>> processor = AutoImageProcessor.from_pretrained(checkpoint)
        >>> model = DepthProForDepthEstimation.from_pretrained(checkpoint)

        >>> device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        >>> model.to(device)

        >>> # prepare image for the model
        >>> inputs = processor(images=image, return_tensors="pt").to(device)

        >>> with torch.no_grad():
        ...     outputs = model(**inputs)

        >>> # interpolate to original size
        >>> post_processed_output = processor.post_process_depth_estimation(
        ...     outputs, target_sizes=[(image.height, image.width)],
        ... )

        >>> # get the field of view (fov) predictions
        >>> field_of_view = post_processed_output[0]["field_of_view"]
        >>> focal_length = post_processed_output[0]["focal_length"]

        >>> # visualize the prediction
        >>> predicted_depth = post_processed_output[0]["predicted_depth"]
        >>> depth = predicted_depth * 255 / predicted_depth.max()
        >>> depth = depth.detach().cpu().numpy()
        >>> depth = Image.fromarray(depth.astype("uint8"))
        ```"""
        loss = None
        if labels is not None:
            raise NotImplementedError("Training is not implemented yet")

        return_dict = return_dict if return_dict is not None else self.config.return_dict
        output_hidden_states = (
            output_hidden_states if output_hidden_states is not None else self.config.output_hidden_states
        )
        output_attentions = output_attentions if output_attentions is not None else self.config.output_attentions

        depth_pro_outputs = self.depth_pro(
            pixel_values=pixel_values,
            output_attentions=output_attentions,
            output_hidden_states=output_hidden_states,
            return_dict=True,
        )
        features = depth_pro_outputs.features
        fused_hidden_states = self.fusion_stage(features)
        predicted_depth = self.head(fused_hidden_states[-1])

        if self.use_fov_model:
            # frozen features from encoder are used
            features_for_fov = features[0].detach()
            fov = self.fov_model(
                pixel_values=pixel_values,
                global_features=features_for_fov,
            )
        else:
            fov = None

        if not return_dict:
            outputs = [loss, predicted_depth, fov, depth_pro_outputs.hidden_states, depth_pro_outputs.attentions]
            return tuple(v for v in outputs if v is not None)

        return DepthProDepthEstimatorOutput(
            loss=loss,
            predicted_depth=predicted_depth,
            field_of_view=fov,
            hidden_states=depth_pro_outputs.hidden_states,
            attentions=depth_pro_outputs.attentions,
        )