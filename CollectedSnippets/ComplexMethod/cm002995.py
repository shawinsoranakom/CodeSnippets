def _preprocess(
        self,
        images: list["torch.Tensor"],
        do_resize: bool,
        size: SizeDict,
        resample: "PILImageResampling | tvF.InterpolationMode | int | None",
        disable_grouping: bool | None,
        return_tensors: str | TensorType | None,
        apply_ocr: bool = True,
        ocr_lang: str | None = None,
        tesseract_config: str | None = None,
        **kwargs,
    ) -> BatchFeature:
        # Tesseract OCR to get words + normalized bounding boxes
        if apply_ocr:
            requires_backends(self, "pytesseract")
            words_batch = []
            boxes_batch = []
            for image in images:
                if image.is_cuda:
                    logger.warning_once(
                        "apply_ocr can only be performed on cpu. Tensors will be transferred to cpu before processing."
                    )
                words, boxes = apply_tesseract(
                    image.cpu(), ocr_lang, tesseract_config, input_data_format=ChannelDimension.FIRST
                )
                words_batch.append(words)
                boxes_batch.append(boxes)

        # Group images by size for batched resizing
        grouped_images, grouped_images_index = group_images_by_shape(images, disable_grouping=disable_grouping)
        resized_images_grouped = {}
        for shape, stacked_images in grouped_images.items():
            if do_resize:
                stacked_images = self.resize(image=stacked_images, size=size, resample=resample)
            resized_images_grouped[shape] = stacked_images
        resized_images = reorder_images(resized_images_grouped, grouped_images_index)

        # Group images by size for further processing
        # Needed in case do_resize is False, or resize returns images with different sizes
        grouped_images, grouped_images_index = group_images_by_shape(resized_images, disable_grouping=disable_grouping)
        processed_images_grouped = {}
        for shape, stacked_images in grouped_images.items():
            # flip color channels from RGB to BGR (as Detectron2 requires this)
            stacked_images = stacked_images.flip(1)
            processed_images_grouped[shape] = stacked_images

        processed_images = reorder_images(processed_images_grouped, grouped_images_index)

        data = BatchFeature(data={"pixel_values": processed_images}, tensor_type=return_tensors)

        if apply_ocr:
            data["words"] = words_batch
            data["boxes"] = boxes_batch

        return data