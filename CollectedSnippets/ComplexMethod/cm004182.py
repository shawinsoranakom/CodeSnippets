def forward(
        self,
        pixel_values: Tensor,
        output_hidden_states: bool | None = None,
        output_attentions: bool | None = None,
        return_dict: bool | None = None,
        **kwargs,
    ) -> BackboneOutput:
        r"""
        Examples:

        ```python
        >>> from transformers import AutoImageProcessor, AutoBackbone
        >>> import torch
        >>> from PIL import Image
        >>> import httpx
        >>> from io import BytesIO

        >>> url = "http://images.cocodataset.org/val2017/000000039769.jpg"
        >>> with httpx.stream("GET", url) as response:
        ...     image = Image.open(BytesIO(response.read()))

        >>> processor = AutoImageProcessor.from_pretrained("microsoft/beit-base-patch16-224")
        >>> model = AutoBackbone.from_pretrained(
        ...     "microsoft/beit-base-patch16-224", out_features=["stage1", "stage2", "stage3", "stage4"]
        ... )

        >>> inputs = processor(image, return_tensors="pt")

        >>> outputs = model(**inputs)
        >>> feature_maps = outputs.feature_maps
        >>> list(feature_maps[-1].shape)
        [1, 768, 14, 14]
        ```"""
        return_dict = return_dict if return_dict is not None else self.config.return_dict
        output_hidden_states = (
            output_hidden_states if output_hidden_states is not None else self.config.output_hidden_states
        )
        output_attentions = output_attentions if output_attentions is not None else self.config.output_attentions

        batch_size = pixel_values.shape[0]
        embedding_output, (patch_height, patch_width) = self.embeddings(pixel_values)
        resolution = pixel_values.shape[2:]

        outputs = self.encoder(
            embedding_output,
            output_hidden_states=True,
            output_attentions=output_attentions,
            resolution=resolution,
            return_dict=return_dict,
        )

        hidden_states = outputs.hidden_states if return_dict else outputs[1]

        feature_maps = ()
        for stage, hidden_state in zip(self.stage_names, hidden_states):
            if stage in self.out_features:
                if self.config.reshape_hidden_states:
                    hidden_state = hidden_state[:, 1:, :]
                    hidden_state = hidden_state.permute(0, 2, 1)
                    hidden_state = hidden_state.reshape(batch_size, -1, patch_height, patch_width)

                feature_maps += (hidden_state,)

        if self.config.add_fpn:
            feature_maps = [
                self.fpn1(feature_maps[0]),
                self.fpn2(feature_maps[1]),
                self.fpn3(feature_maps[2]),
                self.fpn4(feature_maps[3]),
            ]
            feature_maps = tuple(feature_maps)

        if not return_dict:
            if output_hidden_states:
                output = (feature_maps,) + outputs[1:]
            else:
                output = (feature_maps,) + outputs[2:]
            return output

        return BackboneOutput(
            feature_maps=feature_maps,
            hidden_states=outputs.hidden_states if output_hidden_states else None,
            attentions=outputs.attentions,
        )