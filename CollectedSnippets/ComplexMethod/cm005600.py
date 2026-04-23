def postprocess(self, model_outputs, threshold=0.5):
        target_size = model_outputs["target_size"]
        if self.tokenizer is not None:
            # This is a LayoutLMForTokenClassification variant.
            # The OCR got the boxes and the model classified the words.
            height, width = target_size[0].tolist()

            def unnormalize(bbox):
                return self._get_bounding_box(
                    torch.Tensor(
                        [
                            (width * bbox[0] / 1000),
                            (height * bbox[1] / 1000),
                            (width * bbox[2] / 1000),
                            (height * bbox[3] / 1000),
                        ]
                    )
                )

            scores, classes = model_outputs["logits"].squeeze(0).softmax(dim=-1).max(dim=-1)
            labels = [self.model.config.id2label[prediction] for prediction in classes.tolist()]
            boxes = [unnormalize(bbox) for bbox in model_outputs["bbox"].squeeze(0)]
            keys = ["score", "label", "box"]
            annotation = [dict(zip(keys, vals)) for vals in zip(scores.tolist(), labels, boxes) if vals[0] > threshold]
        else:
            # This is a regular ForObjectDetectionModel
            raw_annotations = self.image_processor.post_process_object_detection(model_outputs, threshold, target_size)
            raw_annotation = raw_annotations[0]
            scores = raw_annotation["scores"]
            labels = raw_annotation["labels"]
            boxes = raw_annotation["boxes"]

            raw_annotation["scores"] = scores.tolist()
            raw_annotation["labels"] = [self.model.config.id2label[label.item()] for label in labels]
            raw_annotation["boxes"] = [self._get_bounding_box(box) for box in boxes]

            # {"scores": [...], ...} --> [{"score":x, ...}, ...]
            keys = ["score", "label", "box"]
            annotation = [
                dict(zip(keys, vals))
                for vals in zip(raw_annotation["scores"], raw_annotation["labels"], raw_annotation["boxes"])
            ]

        return annotation