def _parse_and_validate_image_input(
        self, **kwargs: object
    ) -> KananaVImageInputs | None:
        pixel_values = kwargs.pop("pixel_values", None)
        vision_grid_thw = kwargs.pop("vision_grid_thw", None)

        if pixel_values is None:
            return None

        if vision_grid_thw is None:
            raise ValueError(
                "vision_grid_thw is required when pixel_values is provided"
            )

        # Normalize pixel_values to 2D tensor (num_patches, channels*patch*patch)
        if isinstance(pixel_values, torch.Tensor):
            if pixel_values.ndim == 2:
                pass  # Already in expected shape
            elif pixel_values.ndim == 3:
                pixel_values = pixel_values.flatten(0, 1)
            else:
                raise ValueError(
                    f"pixel_values should be 2D or batched 3D tensor. "
                    f"Got ndim: {pixel_values.ndim} "
                    f"(shape={pixel_values.shape})"
                )
        else:
            pixel_values = torch.concat(pixel_values)

        # Normalize vision_grid_thw to 2D tensor (num_images, 3)
        if isinstance(vision_grid_thw, torch.Tensor):
            if vision_grid_thw.ndim == 3:
                vision_grid_thw = vision_grid_thw.flatten(0, 1)
        else:
            vision_grid_thw = torch.concat(vision_grid_thw)

        return KananaVImagePixelInputs(
            type="pixel_values",
            pixel_values=pixel_values,
            vision_grid_thw=vision_grid_thw,
        )