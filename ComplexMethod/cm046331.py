def train(
        self,
        trainer=None,
        **kwargs: Any,
    ):
        """Train the model using the specified dataset and training configuration.

        This method facilitates model training with a range of customizable settings. It supports training with a custom
        trainer or the default training approach. The method handles scenarios such as resuming training from a
        checkpoint, integrating with Ultralytics HUB, and updating model and configuration after training.

        When using Ultralytics HUB, if the session has a loaded model, the method prioritizes HUB training arguments and
        warns if local arguments are provided. It checks for pip updates and combines default configurations,
        method-specific defaults, and user-provided arguments to configure the training process.

        Args:
            trainer (BaseTrainer, optional): Custom trainer instance for model training. If None, uses default.
            **kwargs (Any): Arbitrary keyword arguments for training configuration. Common options include:
                - data (str): Path to dataset configuration file.
                - epochs (int): Number of training epochs.
                - batch (int): Batch size for training.
                - imgsz (int): Input image size.
                - device (str): Device to run training on (e.g., 'cuda', 'cpu').
                - workers (int): Number of worker threads for data loading.
                - optimizer (str): Optimizer to use for training.
                - lr0 (float): Initial learning rate.
                - patience (int): Epochs to wait for no observable improvement for early stopping of training.
                - augmentations (list[Callable]): List of augmentation functions to apply during training.

        Returns:
            (ultralytics.utils.metrics.DetMetrics | None): Training metrics if available and training is successful;
                otherwise, None. The specific metrics type depends on the task.

        Examples:
            >>> model = YOLO("yolo26n.pt")
            >>> results = model.train(data="coco8.yaml", epochs=3)
        """
        self._check_is_pytorch_model()
        if hasattr(self.session, "model") and self.session.model.id:  # Ultralytics HUB session with loaded model
            if any(kwargs):
                LOGGER.warning("using HUB training arguments, ignoring local training arguments.")
            kwargs = self.session.train_args  # overwrite kwargs

        checks.check_pip_update_available()

        overrides = YAML.load(checks.check_yaml(kwargs["cfg"])) if kwargs.get("cfg") else self.overrides
        custom = {
            # NOTE: handle the case when 'cfg' includes 'data'.
            "data": (overrides.get("data") if kwargs.get("cfg") else None)
            or DEFAULT_CFG_DICT["data"]
            or TASK2DATA[self.task],
            "model": self.overrides["model"],
            "task": self.task,
        }  # method defaults
        args = {**overrides, **custom, **kwargs, "mode": "train", "session": self.session}  # prioritizes rightmost args
        if args.get("resume"):
            if args["resume"] is True:  # resume=True (boolean) uses current model as checkpoint
                if self.ckpt and self.ckpt.get("epoch", -1) >= 0 and self.ckpt.get("optimizer") is not None:
                    args["resume"] = self.ckpt_path
                else:
                    LOGGER.warning(
                        f"model '{self.ckpt_path}' is not a resumable training checkpoint "
                        f"(missing epoch/optimizer state). Use 'resume' only to continue incomplete training. "
                        f"Starting new training instead."
                    )
                    args["resume"] = False

        self.trainer = (trainer or self._smart_load("trainer"))(overrides=args, _callbacks=self.callbacks)
        if not args.get("resume") and self.ckpt:
            # Reuse the already-loaded checkpoint model to avoid re-resolving remote weight sources during trainer setup.
            self.trainer.model = self.trainer.get_model(weights=self.model, cfg=self.model.yaml)
            self.model = self.trainer.model

        self.trainer.train()
        # Update model and cfg after training
        if RANK in {-1, 0}:
            ckpt = self.trainer.best if self.trainer.best.exists() else self.trainer.last
            self.model, self.ckpt = load_checkpoint(ckpt)
            self.overrides = self._reset_ckpt_args(self.model.args)
            self.metrics = getattr(self.trainer.validator, "metrics", None)  # TODO: no metrics returned by DDP
        return self.metrics