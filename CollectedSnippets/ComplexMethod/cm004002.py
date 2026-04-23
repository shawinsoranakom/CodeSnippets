def forward(
        self,
        pixel_values: torch.FloatTensor,
        labels: torch.LongTensor | None = None,
        output_hidden_states: bool | None = None,
        return_dict: bool | None = None,
        **kwargs,
    ) -> tuple | SuperPointKeypointDescriptionOutput:
        r"""
        Examples:

        ```python
        >>> from transformers import AutoImageProcessor, SuperPointForKeypointDetection
        >>> import torch
        >>> from PIL import Image
        >>> import httpx
        >>> from io import BytesIO

        >>> url = "http://images.cocodataset.org/val2017/000000039769.jpg"
        >>> with httpx.stream("GET", url) as response:
        ...     image = Image.open(BytesIO(response.read()))

        >>> processor = AutoImageProcessor.from_pretrained("magic-leap-community/superpoint")
        >>> model = SuperPointForKeypointDetection.from_pretrained("magic-leap-community/superpoint")

        >>> inputs = processor(image, return_tensors="pt")
        >>> outputs = model(**inputs)
        ```"""
        loss = None
        if labels is not None:
            raise ValueError("SuperPoint does not support training for now.")

        output_hidden_states = (
            output_hidden_states if output_hidden_states is not None else self.config.output_hidden_states
        )
        return_dict = return_dict if return_dict is not None else self.config.return_dict

        pixel_values = self.extract_one_channel_pixel_values(pixel_values)

        batch_size, _, height, width = pixel_values.shape

        encoder_outputs = self.encoder(
            pixel_values,
            output_hidden_states=output_hidden_states,
            return_dict=return_dict,
        )

        last_hidden_state = encoder_outputs[0]

        list_keypoints_scores = [
            self.keypoint_decoder(last_hidden_state[None, ...]) for last_hidden_state in last_hidden_state
        ]

        list_keypoints = [keypoints_scores[0] for keypoints_scores in list_keypoints_scores]
        list_scores = [keypoints_scores[1] for keypoints_scores in list_keypoints_scores]

        list_descriptors = [
            self.descriptor_decoder(last_hidden_state[None, ...], keypoints[None, ...])
            for last_hidden_state, keypoints in zip(last_hidden_state, list_keypoints)
        ]

        maximum_num_keypoints = max(keypoints.shape[0] for keypoints in list_keypoints)

        keypoints = torch.zeros((batch_size, maximum_num_keypoints, 2), device=pixel_values.device)
        scores = torch.zeros((batch_size, maximum_num_keypoints), device=pixel_values.device)
        descriptors = torch.zeros(
            (batch_size, maximum_num_keypoints, self.config.descriptor_decoder_dim),
            device=pixel_values.device,
        )
        mask = torch.zeros((batch_size, maximum_num_keypoints), device=pixel_values.device, dtype=torch.int)

        for i, (_keypoints, _scores, _descriptors) in enumerate(zip(list_keypoints, list_scores, list_descriptors)):
            keypoints[i, : _keypoints.shape[0]] = _keypoints
            scores[i, : _scores.shape[0]] = _scores
            descriptors[i, : _descriptors.shape[0]] = _descriptors
            mask[i, : _scores.shape[0]] = 1

        # Convert to relative coordinates
        keypoints = keypoints / torch.tensor([width, height], device=keypoints.device)

        hidden_states = encoder_outputs[1] if output_hidden_states else None
        if not return_dict:
            return tuple(v for v in [loss, keypoints, scores, descriptors, mask, hidden_states] if v is not None)

        return SuperPointKeypointDescriptionOutput(
            loss=loss,
            keypoints=keypoints,
            scores=scores,
            descriptors=descriptors,
            mask=mask,
            hidden_states=hidden_states,
        )