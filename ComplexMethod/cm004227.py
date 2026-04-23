def _preprocess(
        self,
        images: list[np.ndarray],
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

        if (
            masks_path is not None
            and format == AnnotationFormat.COCO_PANOPTIC
            and not isinstance(masks_path, (pathlib.Path, str))
        ):
            raise ValueError(
                "The path to the directory containing the mask PNG files should be provided as a"
                f" `pathlib.Path` or string object, but is {type(masks_path)} instead."
            )

        data = {}

        # Import torch if needed for tensor conversion
        if return_tensors == "pt":
            if not is_torch_available():
                raise ImportError("PyTorch is required for tensor conversion.")

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
                        orig_size=get_image_size(image, channel_dim=ChannelDimension.FIRST),
                        target_size=get_image_size(resized_image, channel_dim=ChannelDimension.FIRST),
                    )
                image = resized_image

            if do_rescale:
                image = self.rescale(image, rescale_factor)
            if do_normalize:
                image = self.normalize(image, image_mean, image_std)

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
                padded_size = get_max_height_width(images, input_data_format=ChannelDimension.FIRST)

            padded_images = []
            padded_annotations = []
            for image, annotation in zip(images, annotations if annotations is not None else [None] * len(images)):
                # Pads images and returns their mask: {'pixel_values': ..., 'pixel_mask': ...}
                image_height, image_width = get_image_size(image, channel_dim=ChannelDimension.FIRST)
                if padded_size == (image_height, image_width):
                    padded_images.append(image)
                    pixel_masks.append(np.ones(padded_size, dtype=np.int64))
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
            data.update({"pixel_mask": pixel_masks})

        data.update({"pixel_values": images})
        encoded_inputs = BatchFeature(data, tensor_type=return_tensors)
        if annotations is not None:
            encoded_inputs["labels"] = [
                BatchFeature(annotation, tensor_type=return_tensors) for annotation in annotations
            ]
        return encoded_inputs