def forward(
        self,
        pixel_values: torch.FloatTensor,
        labels: torch.LongTensor | None = None,
        output_attentions: bool | None = None,
        output_hidden_states: bool | None = None,
        return_dict: bool | None = None,
        **kwargs,
    ) -> tuple[torch.Tensor] | DepthEstimatorOutput:
        r"""
        labels (`torch.LongTensor` of shape `(batch_size, height, width)`, *optional*):
            Ground truth depth estimation maps for computing the loss.

        Examples:
        ```python
        >>> from transformers import AutoImageProcessor, ZoeDepthForDepthEstimation
        >>> import torch
        >>> import numpy as np
        >>> from PIL import Image
        >>> import httpx
        >>> from io import BytesIO

        >>> url = "http://images.cocodataset.org/val2017/000000039769.jpg"
        >>> with httpx.stream("GET", url) as response:
        ...     image = Image.open(BytesIO(response.read()))

        >>> image_processor = AutoImageProcessor.from_pretrained("Intel/zoedepth-nyu-kitti")
        >>> model = ZoeDepthForDepthEstimation.from_pretrained("Intel/zoedepth-nyu-kitti")

        >>> # prepare image for the model
        >>> inputs = image_processor(images=image, return_tensors="pt")

        >>> with torch.no_grad():
        ...     outputs = model(**inputs)

        >>> # interpolate to original size
        >>> post_processed_output = image_processor.post_process_depth_estimation(
        ...     outputs,
        ...     source_sizes=[(image.height, image.width)],
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

        return_dict = return_dict if return_dict is not None else self.config.return_dict
        output_hidden_states = (
            output_hidden_states if output_hidden_states is not None else self.config.output_hidden_states
        )
        output_attentions = output_attentions if output_attentions is not None else self.config.output_attentions

        outputs = self.backbone.forward_with_filtered_kwargs(
            pixel_values, output_hidden_states=output_hidden_states, output_attentions=output_attentions
        )
        hidden_states = outputs.feature_maps

        _, _, height, width = pixel_values.shape
        patch_size = self.patch_size
        patch_height = height // patch_size
        patch_width = width // patch_size

        hidden_states, features = self.neck(hidden_states, patch_height, patch_width)

        out = [features] + hidden_states

        relative_depth, features = self.relative_head(hidden_states)

        out = [features] + out

        metric_depth, domain_logits = self.metric_head(
            outconv_activation=out[0], bottleneck=out[1], feature_blocks=out[2:], relative_depth=relative_depth
        )
        metric_depth = metric_depth.squeeze(dim=1)

        if not return_dict:
            if domain_logits is not None:
                output = (metric_depth, domain_logits) + outputs[1:]
            else:
                output = (metric_depth,) + outputs[1:]

            return ((loss,) + output) if loss is not None else output

        return ZoeDepthDepthEstimatorOutput(
            loss=loss,
            predicted_depth=metric_depth,
            domain_logits=domain_logits,
            hidden_states=outputs.hidden_states,
            attentions=outputs.attentions,
        )