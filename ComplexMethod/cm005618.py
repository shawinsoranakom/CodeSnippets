def postprocess(
        self, model_outputs, subtask=None, threshold=0.9, mask_threshold=0.5, overlap_mask_area_threshold=0.5
    ):
        fn = None
        if subtask in {"panoptic", None} and hasattr(self.image_processor, "post_process_panoptic_segmentation"):
            fn = self.image_processor.post_process_panoptic_segmentation
        elif subtask in {"instance", None} and hasattr(self.image_processor, "post_process_instance_segmentation"):
            fn = self.image_processor.post_process_instance_segmentation

        if fn is not None:
            outputs = fn(
                model_outputs,
                threshold=threshold,
                mask_threshold=mask_threshold,
                overlap_mask_area_threshold=overlap_mask_area_threshold,
                target_sizes=model_outputs["target_size"],
            )[0]

            annotation = []
            segmentation = outputs["segmentation"]

            for segment in outputs["segments_info"]:
                mask = (segmentation == segment["id"]) * 255
                mask = Image.fromarray(mask.numpy().astype(np.uint8), mode="L")
                label = self.model.config.id2label[segment["label_id"]]
                score = segment["score"]
                annotation.append({"score": score, "label": label, "mask": mask})

        elif subtask in {"semantic", None} and hasattr(self.image_processor, "post_process_semantic_segmentation"):
            outputs = self.image_processor.post_process_semantic_segmentation(
                model_outputs, target_sizes=model_outputs["target_size"]
            )[0]

            annotation = []
            segmentation = outputs.numpy()
            labels = np.unique(segmentation)

            for label in labels:
                mask = (segmentation == label) * 255
                mask = Image.fromarray(mask.astype(np.uint8), mode="L")
                label = self.model.config.id2label[label]
                annotation.append({"score": None, "label": label, "mask": mask})
        else:
            raise ValueError(f"Subtask {subtask} is not supported for model {type(self.model)}")
        return annotation