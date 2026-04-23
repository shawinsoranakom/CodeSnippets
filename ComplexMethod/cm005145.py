def _preprocess_image_like_inputs(
        self,
        images: ImageInput,
        prompt_depth: ImageInput | None,
        do_convert_rgb: bool,
        input_data_format: ChannelDimension,
        device: Union[str, "torch.device"] | None = None,
        return_tensors: str | TensorType | None = None,
        prompt_scale_to_meter: float | None = None,
        **kwargs,
    ) -> BatchFeature:
        """
        Preprocess image-like inputs, including the main images and optional prompt depth.
        """
        images = self._prepare_image_like_inputs(
            images=images, do_convert_rgb=False, input_data_format=input_data_format, device=device
        )  # always use do_convert_rgb=False rather than defining it as a param to match slow processor

        # Process images with the standard pipeline
        pixel_values = self._preprocess(images, return_tensors=return_tensors, **kwargs)

        data = {"pixel_values": pixel_values}

        # Process prompt depth if provided
        if prompt_depth is not None:
            processed_prompt_depths = self._prepare_image_like_inputs(
                images=prompt_depth,
                do_convert_rgb=False,  # Depth maps should not be converted
                input_data_format=input_data_format,
                device=images[0].device if images else device,
                expected_ndims=2,
            )

            # Validate prompt_depths has same length as images as in slow processor
            if len(processed_prompt_depths) != len(images):
                raise ValueError(
                    f"Number of prompt depth images ({len(processed_prompt_depths)}) does not match number of input images ({len(images)})"
                )

            if prompt_scale_to_meter is None:
                prompt_scale_to_meter = self.prompt_scale_to_meter

            final_prompt_depths = []
            for depth in processed_prompt_depths:
                depth = depth * prompt_scale_to_meter

                # Handle case where depth is constant (min == max)
                if depth.min() == depth.max():
                    depth[0, 0] = depth[0, 0] + 1e-6  # Add small variation to avoid numerical issues

                if depth.ndim == 2:  # Add channel dimension if needed
                    depth = depth.unsqueeze(0)  # [H, W] -> [1, H, W] (channels first)

                depth = depth.float()  # Convert to float32 to match slow processor
                final_prompt_depths.append(depth)

            data["prompt_depth"] = final_prompt_depths

        return BatchFeature(data=data, tensor_type=return_tensors)