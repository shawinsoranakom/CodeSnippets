def forward(
        self,
        pixel_values: Tensor,
        output_hidden_states: bool | None = None,
        return_dict: bool | None = None,
        **kwargs,
    ) -> tuple[tuple] | BackboneOutput:
        r"""
        Examples:

        ```python
        >>> import torch
        >>> import httpx
        >>> from io import BytesIO
        >>> from PIL import Image
        >>> from transformers import AutoImageProcessor, AutoBackbone

        >>> url = "http://images.cocodataset.org/val2017/000000039769.jpg"
        >>> with httpx.stream("GET", url) as response:
        ...     image = Image.open(BytesIO(response.read()))

        >>> processor = AutoImageProcessor.from_pretrained("czczup/textnet-base")
        >>> model = AutoBackbone.from_pretrained("czczup/textnet-base")

        >>> inputs = processor(image, return_tensors="pt")
        >>> with torch.no_grad():
        >>>     outputs = model(**inputs)
        ```"""
        return_dict = return_dict if return_dict is not None else self.config.return_dict
        output_hidden_states = (
            output_hidden_states if output_hidden_states is not None else self.config.output_hidden_states
        )

        outputs = self.textnet(pixel_values, output_hidden_states=True, return_dict=return_dict)

        hidden_states = outputs.hidden_states if return_dict else outputs[2]

        feature_maps = ()
        for idx, stage in enumerate(self.stage_names):
            if stage in self.out_features:
                feature_maps += (hidden_states[idx],)

        if not return_dict:
            output = (feature_maps,)
            if output_hidden_states:
                hidden_states = outputs.hidden_states if return_dict else outputs[2]
                output += (hidden_states,)
            return output

        return BackboneOutput(
            feature_maps=feature_maps,
            hidden_states=outputs.hidden_states if output_hidden_states else None,
            attentions=None,
        )