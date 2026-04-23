def __init__(self, opt, console_logger, include=("tb", "wandb", "clearml")):
        """Initializes a generic logger with optional TensorBoard, W&B, and ClearML support."""
        self.save_dir = Path(opt.save_dir)
        self.include = include
        self.console_logger = console_logger
        self.csv = self.save_dir / "results.csv"  # CSV logger
        if "tb" in self.include:
            prefix = colorstr("TensorBoard: ")
            self.console_logger.info(
                f"{prefix}Start with 'tensorboard --logdir {self.save_dir.parent}', view at http://localhost:6006/"
            )
            self.tb = SummaryWriter(str(self.save_dir))

        if wandb and "wandb" in self.include:
            self.wandb = wandb.init(
                project=web_project_name(str(opt.project)), name=None if opt.name == "exp" else opt.name, config=opt
            )
        else:
            self.wandb = None

        if clearml and "clearml" in self.include:
            try:
                # Hyp is not available in classification mode
                hyp = {} if "hyp" not in opt else opt.hyp
                self.clearml = ClearmlLogger(opt, hyp)
            except Exception:
                self.clearml = None
                prefix = colorstr("ClearML: ")
                LOGGER.warning(
                    f"{prefix}WARNING ⚠️ ClearML is installed but not configured, skipping ClearML logging."
                    f" See https://docs.ultralytics.com/yolov5/tutorials/clearml_logging_integration"
                )
        else:
            self.clearml = None