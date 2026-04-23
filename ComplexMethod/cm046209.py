def predict(
        self,
        source=None,
        stream: bool = False,
        visual_prompts: dict[str, list] = {},
        refer_image=None,
        predictor=yolo.yoloe.YOLOEVPDetectPredictor,
        **kwargs,
    ):
        """Run prediction on images, videos, directories, streams, etc.

        Args:
            source (str | int | PIL.Image | np.ndarray, optional): Source for prediction. Accepts image paths, directory
                paths, URL/YouTube streams, PIL images, numpy arrays, or webcam indices.
            stream (bool): Whether to stream the prediction results. If True, results are yielded as a generator as they
                are computed.
            visual_prompts (dict[str, list]): Dictionary containing visual prompts for the model. Must include 'bboxes'
                and 'cls' keys when non-empty.
            refer_image (str | PIL.Image | np.ndarray, optional): Reference image for visual prompts.
            predictor (callable): Custom predictor class for visual prompt predictions. Defaults to
                YOLOEVPDetectPredictor.
            **kwargs (Any): Additional keyword arguments passed to the predictor.

        Returns:
            (list | generator): List of Results objects or generator of Results objects if stream=True.

        Examples:
            >>> model = YOLOE("yoloe-11s-seg.pt")
            >>> results = model.predict("path/to/image.jpg")
            >>> # With visual prompts
            >>> prompts = {"bboxes": [[10, 20, 100, 200]], "cls": ["person"]}
            >>> results = model.predict("path/to/image.jpg", visual_prompts=prompts)
        """
        if len(visual_prompts):
            assert "bboxes" in visual_prompts and "cls" in visual_prompts, (
                f"Expected 'bboxes' and 'cls' in visual prompts, but got {visual_prompts.keys()}"
            )
            assert len(visual_prompts["bboxes"]) == len(visual_prompts["cls"]), (
                f"Expected equal number of bounding boxes and classes, but got {len(visual_prompts['bboxes'])} and "
                f"{len(visual_prompts['cls'])} respectively"
            )
            if type(self.predictor) is not predictor:
                self.predictor = predictor(
                    overrides={
                        "task": self.model.task,
                        "mode": "predict",
                        "save": False,
                        "verbose": refer_image is None,
                        "batch": 1,
                        "device": kwargs.get("device", None),
                        "half": kwargs.get("half", False),
                        "imgsz": kwargs.get("imgsz", self.overrides.get("imgsz", 640)),
                    },
                    _callbacks=self.callbacks,
                )

            num_cls = (
                max(len(set(c)) for c in visual_prompts["cls"])
                if isinstance(source, list) and refer_image is None  # means multiple images
                else len(set(visual_prompts["cls"]))
            )
            self.model.model[-1].nc = num_cls
            self.model.names = [f"object{i}" for i in range(num_cls)]
            self.predictor.set_prompts(visual_prompts.copy())
            self.predictor.setup_model(model=self.model)

            if refer_image is None and source is not None:
                dataset = load_inference_source(source)
                if dataset.mode in {"video", "stream"}:
                    # NOTE: set the first frame as refer image for videos/streams inference
                    refer_image = next(iter(dataset))[1][0]
            if refer_image is not None:
                vpe = self.predictor.get_vpe(refer_image)
                self.model.set_classes(self.model.names, vpe)
                self.task = "segment" if isinstance(self.predictor, yolo.segment.SegmentationPredictor) else "detect"
                self.predictor = None  # reset predictor
        elif isinstance(self.predictor, yolo.yoloe.YOLOEVPDetectPredictor):
            self.predictor = None  # reset predictor if no visual prompts
        self.overrides["agnostic_nms"] = True  # use agnostic nms for YOLOE default

        return super().predict(source, stream, **kwargs)