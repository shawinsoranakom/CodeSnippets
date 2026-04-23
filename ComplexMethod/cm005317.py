def _preprocess(
        self,
        images: list[np.ndarray],
        do_resize: bool,
        size: SizeDict,
        resample: PILImageResampling | None,
        do_center_crop: bool,
        crop_size: SizeDict,
        do_rescale: bool,
        rescale_factor: float,
        do_normalize: bool,
        image_mean: float | list[float] | None,
        image_std: float | list[float] | None,
        do_pad: bool | None,
        pad_size: SizeDict | None,
        return_tensors: str | TensorType | None,
        do_affine_transform: bool = True,
        normalize_factor: float = 200.0,
        boxes: list | np.ndarray | None = None,
        **kwargs,
    ) -> BatchFeature:
        """Custom preprocessing for VitPose."""
        if boxes is not None and do_affine_transform:
            transformed_images = []
            for image, image_boxes in zip(images, boxes):
                for box in image_boxes:
                    center, scale = box_to_center_and_scale(
                        box, image_width=size.width, image_height=size.height, normalize_factor=normalize_factor
                    )
                    transformed_image = self.affine_transform(image, center, scale, rotation=0, size=size)
                    transformed_images.append(transformed_image)
            images = transformed_images

        processed_images = []
        for image in images:
            if do_rescale:
                image = self.rescale(image, rescale_factor)
            if do_normalize:
                image = self.normalize(image, image_mean, image_std)
            processed_images.append(image)
        return BatchFeature(data={"pixel_values": processed_images}, tensor_type=return_tensors)