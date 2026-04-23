def _preprocess_image_like_inputs(
        self,
        images: ImageInput,
        prompt_images: ImageInput | None,
        prompt_masks: ImageInput | None,
        do_convert_rgb: bool,
        input_data_format: ChannelDimension,
        return_tensors: str | TensorType | None,
        num_labels: int | None = None,
        **kwargs,
    ) -> BatchFeature:
        data = {}

        # Process regular images (do_convert_rgb=False: assume RGB, no mask conversion)
        # Check for the empty-list sentinel passed when images=None
        _images_provided = not (isinstance(images, list) and len(images) == 0)
        if _images_provided:
            prepared_images = self._prepare_image_like_inputs(
                images=images, do_convert_rgb=False, input_data_format=input_data_format
            )
            data["pixel_values"] = self._preprocess(prepared_images, **kwargs)

        # Process prompt images (same as regular images)
        if prompt_images is not None:
            prepared_prompt_images = self._prepare_image_like_inputs(
                images=prompt_images, do_convert_rgb=False, input_data_format=input_data_format
            )
            data["prompt_pixel_values"] = self._preprocess(prepared_prompt_images, **kwargs)

        # Process prompt masks with special handling
        if prompt_masks is not None:
            if do_convert_rgb:
                # 2D segmentation maps → convert to 3-channel RGB via palette
                prepared_masks = self._prepare_image_like_inputs(
                    images=prompt_masks,
                    expected_ndims=2,
                    do_convert_rgb=False,
                    input_data_format=ChannelDimension.FIRST,
                )
                palette = self.get_palette(num_labels) if num_labels is not None else None
                prepared_masks = [self.mask_to_rgb(mask, palette=palette) for mask in prepared_masks]
            else:
                # Already 3-channel RGB masks
                prepared_masks = self._prepare_image_like_inputs(
                    images=prompt_masks, expected_ndims=3, do_convert_rgb=False, input_data_format=input_data_format
                )

            masks_kwargs = dict(kwargs)
            masks_kwargs["resample"] = PILImageResampling.NEAREST
            data["prompt_masks"] = self._preprocess(prepared_masks, **masks_kwargs)

        return BatchFeature(data=data, tensor_type=return_tensors)