def comm_get_image_processing_inputs(
        self,
        image_processor_tester,
        image_processing_class,
        with_segmentation_maps=False,
        is_instance_map=False,
        segmentation_type="np",
        numpify=False,
        input_data_format=None,
    ):
        image_processing = image_processing_class(**image_processor_tester.prepare_image_processor_dict())
        # prepare image and target
        num_labels = image_processor_tester.num_labels
        annotations = None
        instance_id_to_semantic_id = None
        image_inputs = image_processor_tester.prepare_image_inputs(equal_resolution=False, numpify=numpify)
        if with_segmentation_maps:
            high = num_labels
            if is_instance_map:
                labels_expanded = list(range(num_labels)) * 2
                instance_id_to_semantic_id = dict(enumerate(labels_expanded))
            annotations = [
                np.random.randint(0, high * 2, img.shape[:2] if numpify else (img.size[1], img.size[0])).astype(
                    np.uint8
                )
                for img in image_inputs
            ]
            if segmentation_type == "pil":
                annotations = [Image.fromarray(annotation) for annotation in annotations]

        if input_data_format is ChannelDimension.FIRST and numpify:
            image_inputs = [np.moveaxis(img, -1, 0) for img in image_inputs]

        inputs = image_processing(
            image_inputs,
            annotations,
            return_tensors="pt",
            instance_id_to_semantic_id=instance_id_to_semantic_id,
            input_data_format=input_data_format,
        )

        return inputs