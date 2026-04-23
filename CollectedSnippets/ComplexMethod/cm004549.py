def forward(
        self,
        pixel_values: torch.FloatTensor,
        labels: torch.LongTensor | None = None,
        output_attentions: bool | None = None,
        output_hidden_states: bool | None = None,
        return_dict: bool | None = None,
        **kwargs,
    ) -> tuple | SuperGlueKeypointMatchingOutput:
        r"""
        Examples:

        ```python
        >>> from transformers import AutoImageProcessor, AutoModel
        >>> import torch
        >>> from PIL import Image
        >>> import httpx
        >>> from io import BytesIO

        >>> url = "https://github.com/magicleap/SuperGluePretrainedNetwork/blob/master/assets/phototourism_sample_images/london_bridge_78916675_4568141288.jpg?raw=true"
        >>> with httpx.stream("GET", url) as response:
        ...     image_1 = Image.open(BytesIO(response.read()))

        >>> url = "https://github.com/magicleap/SuperGluePretrainedNetwork/blob/master/assets/phototourism_sample_images/london_bridge_19481797_2295892421.jpg?raw=true"
        >>> with httpx.stream("GET", url) as response:
        ...     image_2 = Image.open(BytesIO(response.read()))

        >>> images = [image_1, image_2]

        >>> processor = AutoImageProcessor.from_pretrained("magic-leap-community/superglue_outdoor")
        >>> model = AutoModel.from_pretrained("magic-leap-community/superglue_outdoor")

        >>> with torch.no_grad():
        >>>     inputs = processor(images, return_tensors="pt")
        >>>     outputs = model(**inputs)
        ```"""
        loss = None
        if labels is not None:
            raise ValueError("SuperGlue is not trainable, no labels should be provided.")

        output_attentions = output_attentions if output_attentions is not None else self.config.output_attentions
        output_hidden_states = (
            output_hidden_states if output_hidden_states is not None else self.config.output_hidden_states
        )
        return_dict = return_dict if return_dict is not None else self.config.return_dict

        if pixel_values.ndim != 5 or pixel_values.size(1) != 2:
            raise ValueError("Input must be a 5D tensor of shape (batch_size, 2, num_channels, height, width)")

        batch_size, _, channels, height, width = pixel_values.shape
        pixel_values = pixel_values.reshape(batch_size * 2, channels, height, width)
        keypoint_detections = self.keypoint_detector(pixel_values)

        keypoints, scores, descriptors, mask = keypoint_detections[:4]
        keypoints = keypoints.reshape(batch_size, 2, -1, 2).to(pixel_values)
        scores = scores.reshape(batch_size, 2, -1).to(pixel_values)
        descriptors = descriptors.reshape(batch_size, 2, -1, self.config.hidden_size).to(pixel_values)
        mask = mask.reshape(batch_size, 2, -1)

        absolute_keypoints = keypoints.clone()
        absolute_keypoints[:, :, :, 0] = absolute_keypoints[:, :, :, 0] * width
        absolute_keypoints[:, :, :, 1] = absolute_keypoints[:, :, :, 1] * height

        matches, matching_scores, hidden_states, attentions = self._match_image_pair(
            absolute_keypoints,
            descriptors,
            scores,
            height,
            width,
            mask=mask,
            output_attentions=output_attentions,
            output_hidden_states=output_hidden_states,
        )

        if not return_dict:
            return tuple(
                v
                for v in [loss, matches, matching_scores, keypoints, mask, hidden_states, attentions]
                if v is not None
            )

        return SuperGlueKeypointMatchingOutput(
            loss=loss,
            matches=matches,
            matching_scores=matching_scores,
            keypoints=keypoints,
            mask=mask,
            hidden_states=hidden_states,
            attentions=attentions,
        )