def _parse_and_validate_image_input(
        self, **kwargs: object
    ) -> OvisImagePatchInputs | None:
        pixel_values = kwargs.pop("pixel_values", None)
        indicator_tokens = kwargs.pop("indicator_tokens", None)

        if pixel_values is None and indicator_tokens is None:
            return None

        if pixel_values is not None and indicator_tokens is not None:
            if not isinstance(pixel_values, (torch.Tensor, list)):
                raise ValueError(
                    f"Incorrect type of pixel values. Got type: {type(pixel_values)}"
                )

            if not isinstance(indicator_tokens, (torch.Tensor, list)):
                raise ValueError(
                    "Incorrect type of indicator_tokens. "
                    f"Got type: {type(pixel_values)}"
                )

            return OvisImagePatchInputs(
                type="image_patches",
                flat_data=flatten_bn(pixel_values, concat=True),
                patches_per_image=[x.shape[0] for x in pixel_values],
                indicator_tokens=flatten_bn(indicator_tokens, concat=True),
            )

        raise AssertionError("This line should be unreachable.")