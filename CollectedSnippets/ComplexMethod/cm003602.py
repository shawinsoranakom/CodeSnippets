def postprocess(
        self,
        images: ImageInput,
        do_rescale: bool | None = None,
        rescale_factor: float | None = None,
        do_normalize: bool | None = None,
        image_mean: list[float] | None = None,
        image_std: list[float] | None = None,
        input_data_format: str | None = None,
        return_tensors: str | None = None,
    ):
        """Applies post-processing to the decoded image tokens by reversing transformations applied during preprocessing."""
        do_rescale = do_rescale if do_rescale is not None else self.do_rescale
        rescale_factor = 1.0 / self.rescale_factor if rescale_factor is None else rescale_factor
        do_normalize = do_normalize if do_normalize is not None else self.do_normalize
        image_mean = image_mean if image_mean is not None else self.image_mean
        image_std = image_std if image_std is not None else self.image_std

        images = make_flat_list_of_images(images)  # Ensures input is a list

        if isinstance(images[0], PIL.Image.Image):
            return images if len(images) > 1 else images[0]

        if input_data_format is None:
            input_data_format = infer_channel_dimension_format(images[0])  # Determine format dynamically

        pixel_values = []

        for image in images:
            image = to_numpy_array(image)  # Ensure NumPy format

            if do_normalize:
                image = self.unnormalize(
                    image=image, image_mean=image_mean, image_std=image_std, input_data_format=input_data_format
                )

            if do_rescale:
                image = self.rescale(image, scale=rescale_factor, input_data_format=input_data_format)
                image = image.clip(0, 255).astype(np.uint8)

            if do_normalize and do_rescale and return_tensors == "PIL.Image.Image":
                image = to_channel_dimension_format(image, ChannelDimension.LAST, input_channel_dim=input_data_format)
                image = PIL.Image.fromarray(image)

            pixel_values.append(image)

        data = {"pixel_values": pixel_values}
        return_tensors = return_tensors if return_tensors != "PIL.Image.Image" else None

        return BatchFeature(data=data, tensor_type=return_tensors)