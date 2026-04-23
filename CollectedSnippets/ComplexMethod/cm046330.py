def predict(
        self,
        source: str | Path | int | Image.Image | list | tuple | np.ndarray | torch.Tensor = None,
        stream: bool = False,
        predictor=None,
        **kwargs: Any,
    ) -> list[Results]:
        """Perform predictions on the given image source using the YOLO model.

        This method facilitates the prediction process, allowing various configurations through keyword arguments. It
        supports predictions with custom predictors or the default predictor method. The method handles different types
        of image sources and can operate in a streaming mode.

        Args:
            source (str | Path | int | PIL.Image | np.ndarray | torch.Tensor | list | tuple): The source of the image(s)
                to make predictions on. Accepts various types including file paths, URLs, PIL images, numpy arrays, and
                torch tensors.
            stream (bool): If True, treats the input source as a continuous stream for predictions.
            predictor (BasePredictor, optional): An instance of a custom predictor class for making predictions. If
                None, the method uses a default predictor.
            **kwargs (Any): Additional keyword arguments for configuring the prediction process.

        Returns:
            (list[ultralytics.engine.results.Results]): A list of prediction results, each encapsulated in a Results
                object.

        Examples:
            >>> model = YOLO("yolo26n.pt")
            >>> results = model.predict(source="path/to/image.jpg", conf=0.25)
            >>> for r in results:
            ...     print(r.boxes.data)  # print detection bounding boxes

        Notes:
            - If 'source' is not provided, it defaults to the ASSETS constant with a warning.
            - The method sets up a new predictor if not already present and updates its arguments with each call.
            - For SAM-type models, 'prompts' can be passed as a keyword argument.
        """
        if source is None:
            source = "https://ultralytics.com/images/boats.jpg" if self.task == "obb" else ASSETS
            LOGGER.warning(f"'source' is missing. Using 'source={source}'.")

        is_cli = (ARGV[0].endswith("yolo") or ARGV[0].endswith("ultralytics")) and any(
            x in ARGV for x in ("predict", "track", "mode=predict", "mode=track")
        )

        custom = {"conf": 0.25, "batch": 1, "save": is_cli, "mode": "predict", "rect": True}  # method defaults
        args = {**self.overrides, **custom, **kwargs}  # highest priority args on the right
        prompts = args.pop("prompts", None)  # for SAM-type models

        if not self.predictor or self.predictor.args.device != args.get("device", self.predictor.args.device):
            self.predictor = (predictor or self._smart_load("predictor"))(overrides=args, _callbacks=self.callbacks)
            self.predictor.setup_model(model=self.model, verbose=is_cli)
        else:  # only update args if predictor is already setup
            self.predictor.args = get_cfg(self.predictor.args, args)
            if "project" in args or "name" in args:
                self.predictor.save_dir = get_save_dir(self.predictor.args)
        if prompts and hasattr(self.predictor, "set_prompts"):  # for SAM-type models
            self.predictor.set_prompts(prompts)
        return self.predictor.predict_cli(source=source) if is_cli else self.predictor(source=source, stream=stream)