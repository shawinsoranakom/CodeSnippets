def _preprocess(
        self,
        images: list[np.ndarray],
        do_resize: bool,
        size: SizeDict,
        resample: "PILImageResampling | None",
        do_rescale: bool,
        rescale_factor: float,
        do_normalize: bool,
        image_mean: float | list[float] | None,
        image_std: float | list[float] | None,
        return_tensors: str | TensorType | None,
        do_color_quantize: bool | None = None,
        clusters: "list | np.ndarray | torch.Tensor | None" = None,
        **kwargs,
    ):
        processed_images = []
        for image in images:
            if do_resize:
                image = self.resize(image, size, resample)
            if do_rescale:
                image = self.rescale(image, rescale_factor)
            if do_normalize:
                image = self.normalize(image, image_mean, image_std)
            processed_images.append(image)

        # If color quantization is requested, perform it; otherwise return pixel values
        if do_color_quantize:
            # Prepare clusters
            if clusters is None:
                raise ValueError("Clusters must be provided for color quantization.")
            # Convert to numpy array if needed
            clusters_np = np.array(clusters) if not isinstance(clusters, np.ndarray) else clusters

            # Stack channel-first images (B, C, H, W) and transpose to (B, H, W, C) for color quantization
            images_array = np.array(processed_images)
            images_hwc = images_array.transpose(0, 2, 3, 1)
            input_ids = color_quantize(images_hwc, clusters_np).reshape(
                images_array.shape[0], images_array.shape[2], images_array.shape[3]
            )

            # flatten to (batch_size, height*width)
            batch_size = input_ids.shape[0]
            input_ids = input_ids.reshape(batch_size, -1)

            # We need to convert back to a list to keep consistent behaviour across processors.
            input_ids = list(input_ids)
            return BatchFeature(data={"input_ids": input_ids}, tensor_type=return_tensors)

        return BatchFeature(data={"pixel_values": processed_images}, tensor_type=return_tensors)