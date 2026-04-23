def _preprocess(
        self,
        images: list["torch.Tensor"],
        annotations: AnnotationType | list[AnnotationType] | None,
        return_segmentation_masks: bool,
        masks_path: str | pathlib.Path | None,
        do_resize: bool,
        size: SizeDict,
        resample: "PILImageResampling | None",
        do_rescale: bool,
        rescale_factor: float,
        do_normalize: bool,
        do_convert_annotations: bool,
        image_mean: float | list[float] | None,
        image_std: float | list[float] | None,
        do_pad: bool,
        pad_size: SizeDict | None,
        format: str | AnnotationFormat | None,
        return_tensors: str | TensorType | None,
        **kwargs,
    ) -> BatchFeature:
        """
        Preprocess an image or a batch of images so that it can be used by the model.
        """

        if annotations is not None and isinstance(annotations, dict):
            annotations = [annotations]

        if annotations is not None and len(images) != len(annotations):
            raise ValueError(
                f"The number of images ({len(images)}) and annotations ({len(annotations)}) do not match."
            )

        format = AnnotationFormat(format)
        if annotations is not None:
            validate_annotations(format, SUPPORTED_ANNOTATION_FORMATS, annotations)

        data = {}
        processed_images = []
        processed_annotations = []
        pixel_masks = []  # Initialize pixel_masks here
        for image, annotation in zip(images, annotations if annotations is not None else [None] * len(images)):
            # prepare (COCO annotations as a list of Dict -> DETR target as a single Dict per image)
            if annotations is not None:
                annotation = self.prepare_annotation(
                    image,
                    annotation,
                    format,
                    return_segmentation_masks=return_segmentation_masks,
                    masks_path=masks_path,
                    input_data_format=ChannelDimension.FIRST,
                )

            if do_resize:
                resized_image = self.resize(image, size=size, resample=resample)
                if annotations is not None:
                    annotation = self.resize_annotation(
                        annotation,
                        orig_size=image.size()[-2:],
                        target_size=resized_image.size()[-2:],
                    )
                image = resized_image
            # Fused rescale and normalize
            image = self.rescale_and_normalize(image, do_rescale, rescale_factor, do_normalize, image_mean, image_std)
            if do_convert_annotations and annotations is not None:
                annotation = self.normalize_annotation(annotation, get_image_size(image, ChannelDimension.FIRST))

            processed_images.append(image)
            processed_annotations.append(annotation)
        images = processed_images
        annotations = processed_annotations if annotations is not None else None

        if do_pad:
            # depends on all resized image shapes so we need another loop
            if pad_size is not None:
                padded_size = (pad_size.height, pad_size.width)
            else:
                padded_size = get_max_height_width(images)

            padded_images = []
            padded_annotations = []
            for image, annotation in zip(images, annotations if annotations is not None else [None] * len(images)):
                # Pads images and returns their mask: {'pixel_values': ..., 'pixel_mask': ...}
                if padded_size == image.size()[-2:]:
                    padded_images.append(image)
                    pixel_masks.append(torch.ones(padded_size, dtype=torch.int64, device=image.device))
                    padded_annotations.append(annotation)
                    continue
                image, pixel_mask, annotation = self.pad(
                    image, padded_size, annotation=annotation, update_bboxes=do_convert_annotations
                )
                padded_images.append(image)
                padded_annotations.append(annotation)
                pixel_masks.append(pixel_mask)
            images = padded_images
            annotations = padded_annotations if annotations is not None else None
            data.update({"pixel_mask": torch.stack(pixel_masks, dim=0)})

        data.update({"pixel_values": torch.stack(images, dim=0)})
        encoded_inputs = BatchFeature(data, tensor_type=return_tensors)
        if annotations is not None:
            encoded_inputs["labels"] = [
                BatchFeature(annotation, tensor_type=return_tensors) for annotation in annotations
            ]
        return encoded_inputs