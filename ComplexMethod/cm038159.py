def _parse_and_validate_image_input(
        self, **kwargs: object
    ) -> Eagle2_5_VLImageInputs | None:
        """Parse and validate image inputs."""
        pixel_values_flat = kwargs.pop("pixel_values_flat", None)
        image_num_patches = kwargs.pop("image_num_patches", None)
        image_embeds = kwargs.pop("image_embeds", None)

        if pixel_values_flat is None and image_embeds is None:
            return None

        if image_embeds is not None:
            return Eagle2_5_VLImageEmbeddingInputs(
                type="image_embeds",
                data=image_embeds,
            )

        image_token_id = kwargs.get("image_token_id")
        if image_token_id is not None:
            if isinstance(image_token_id, torch.Tensor):
                image_token_id = image_token_id.flatten().unique().item()
            assert isinstance(image_token_id, int)
            self.img_context_token_id = image_token_id

        if pixel_values_flat is not None:
            image_size = getattr(self.config, "force_image_size", None)
            if image_size is None:
                image_size = self.config.vision_config.image_size
            expected_h = expected_w = image_size
            resolve_bindings = {"h": expected_h, "w": expected_w}

            return Eagle2_5_VLImagePixelInputs(
                type="pixel_values",
                pixel_values_flat=pixel_values_flat,
                num_patches=image_num_patches,
                resolve_bindings=resolve_bindings,
            )

        raise AssertionError("This line should be unreachable.")