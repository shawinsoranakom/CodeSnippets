def post_process_generation(self, text=None, sequence=None, task=None, image_size=None) -> dict[str, Any]:
        """
        Post-process generation outputs based on the task.

        Args:
            text (`str`, *optional*):
                Generated text.
            sequence (`Union[List[int], torch.Tensor]`, *optional*):
                Generated token sequence.
            task (`str`, *optional*):
                The task for post-processing.
            image_size (`Tuple[int, int]`, *optional*):
                Image size for dequantization.

        Returns:
            `Dict[str, Any]`: Post-processed results keyed by task.
        """
        if task is None:
            raise ValueError("`task` must be provided for post-processing.")

        post_proc_type = self.tasks_answer_post_processing_type.get(task, "pure_text")
        parsed = self.post_processor(
            text=text,
            sequence=sequence,
            image_size=image_size,
            parse_tasks=[post_proc_type],
        )[post_proc_type]

        if post_proc_type == "pure_text":
            final_answer = parsed.replace("<s>", "").replace("</s>", "").strip()
        elif post_proc_type in ["description_with_bboxes", "bboxes"]:
            bboxes = [inst["bbox"] for inst in parsed]
            labels = [inst["cat_name"] for inst in parsed]
            final_answer = {"bboxes": bboxes, "labels": labels}
            if parsed and "score" in parsed[0]:
                final_answer["scores"] = [inst["score"] for inst in parsed]
        elif post_proc_type == "ocr":
            quad_boxes = [inst["quad_box"] for inst in parsed]
            labels = [inst["text"] for inst in parsed]
            final_answer = {"quad_boxes": quad_boxes, "labels": labels}
        elif post_proc_type == "phrase_grounding":
            bboxes = []
            labels = []
            for inst in parsed:
                for bbox in inst["bbox"]:
                    bboxes.append(bbox)
                    labels.append(inst["cat_name"])
            final_answer = {"bboxes": bboxes, "labels": labels}
        elif post_proc_type in ["description_with_polygons", "polygons"]:
            polygons = [inst["polygons"] for inst in parsed]
            labels = [inst["cat_name"] for inst in parsed]
            final_answer = {"polygons": polygons, "labels": labels}
        elif post_proc_type == "description_with_bboxes_or_polygons":
            bboxes = []
            bboxes_labels = []
            polygons = []
            polygons_labels = []
            for inst in parsed:
                label = inst["cat_name"]
                if "polygons" in inst:
                    polygons.append(inst["polygons"])
                    polygons_labels.append(label)
                else:
                    bboxes.append(inst["bbox"])
                    bboxes_labels.append(label)
            final_answer = {
                "bboxes": bboxes,
                "bboxes_labels": bboxes_labels,
                "polygons": polygons,
                "polygons_labels": polygons_labels,
            }
        else:
            raise ValueError(f"Unknown post-processing type: {post_proc_type}")

        return {task: final_answer}