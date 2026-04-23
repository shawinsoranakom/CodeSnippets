def _preprocess(
        self,
        images: list[np.ndarray],
        task_inputs: list[str] | None,
        segmentation_maps: list[np.ndarray],
        instance_id_to_semantic_id: list[dict[int, int]] | dict[int, int] | None,
        do_resize: bool,
        size: SizeDict,
        resample: PILImageResampling | None,
        do_rescale: bool,
        rescale_factor: float,
        do_normalize: bool,
        image_mean: float | list[float] | None,
        image_std: float | list[float] | None,
        ignore_index: int | None,
        do_reduce_labels: bool | None,
        return_tensors: str | TensorType | None,
        **kwargs,
    ) -> BatchFeature:
        # Process images one by one (no batching in PIL backend)
        processed_images = []
        processed_segmentation_maps = None
        if segmentation_maps is not None:
            processed_segmentation_maps = []

        for idx, image in enumerate(images):
            if do_resize:
                image = self.resize(image=image, size=size, resample=resample)
            if do_rescale:
                image = self.rescale(image, rescale_factor)
            if do_normalize:
                image = self.normalize(image, image_mean, image_std)
            processed_images.append(image)

            if segmentation_maps is not None:
                seg_map = segmentation_maps[idx]
                if do_resize:
                    seg_map = self.resize(image=seg_map, size=size, resample=PILImageResampling.NEAREST)
                processed_segmentation_maps.append(seg_map)

        encoded_inputs = self.encode_inputs(
            processed_images,
            task_inputs,
            segmentation_maps=processed_segmentation_maps,
            instance_id_to_semantic_id=instance_id_to_semantic_id,
            ignore_index=ignore_index,
            do_reduce_labels=do_reduce_labels,
            return_tensors=return_tensors,
        )

        return encoded_inputs