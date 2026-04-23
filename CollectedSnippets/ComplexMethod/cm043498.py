def __init__(self, save_dir=None, weights=None, opt=None, hyp=None, logger=None, include=LOGGERS):
        """Initializes loggers for YOLOv5 training and validation metrics, paths, and options."""
        self.save_dir = save_dir
        self.weights = weights
        self.opt = opt
        self.hyp = hyp
        self.plots = not opt.noplots  # plot results
        self.logger = logger  # for printing results to console
        self.include = include
        self.keys = [
            "train/box_loss",
            "train/obj_loss",
            "train/cls_loss",  # train loss
            "metrics/precision",
            "metrics/recall",
            "metrics/mAP_0.5",
            "metrics/mAP_0.5:0.95",  # metrics
            "val/box_loss",
            "val/obj_loss",
            "val/cls_loss",  # val loss
            "x/lr0",
            "x/lr1",
            "x/lr2",
        ]  # params
        self.best_keys = ["best/epoch", "best/precision", "best/recall", "best/mAP_0.5", "best/mAP_0.5:0.95"]
        for k in LOGGERS:
            setattr(self, k, None)  # init empty logger dictionary
        self.csv = True  # always log to csv
        self.ndjson_console = "ndjson_console" in self.include  # log ndjson to console
        self.ndjson_file = "ndjson_file" in self.include  # log ndjson to file

        # Messages
        if not comet_ml:
            prefix = colorstr("Comet: ")
            s = f"{prefix}run 'pip install comet_ml' to automatically track and visualize YOLOv5 🚀 runs in Comet"
            self.logger.info(s)
        # TensorBoard
        s = self.save_dir
        if "tb" in self.include and not self.opt.evolve:
            prefix = colorstr("TensorBoard: ")
            self.logger.info(f"{prefix}Start with 'tensorboard --logdir {s.parent}', view at http://localhost:6006/")
            self.tb = SummaryWriter(str(s))

        # W&B
        if wandb and "wandb" in self.include:
            self.opt.hyp = self.hyp  # add hyperparameters
            self.wandb = WandbLogger(self.opt)
        else:
            self.wandb = None

        # ClearML
        if clearml and "clearml" in self.include:
            try:
                self.clearml = ClearmlLogger(self.opt, self.hyp)
            except Exception:
                self.clearml = None
                prefix = colorstr("ClearML: ")
                LOGGER.warning(
                    f"{prefix}WARNING ⚠️ ClearML is installed but not configured, skipping ClearML logging."
                    f" See https://docs.ultralytics.com/yolov5/tutorials/clearml_logging_integration#readme"
                )

        else:
            self.clearml = None

        # Comet
        if comet_ml and "comet" in self.include:
            if isinstance(self.opt.resume, str) and self.opt.resume.startswith("comet://"):
                run_id = self.opt.resume.split("/")[-1]
                self.comet_logger = CometLogger(self.opt, self.hyp, run_id=run_id)

            else:
                self.comet_logger = CometLogger(self.opt, self.hyp)

        else:
            self.comet_logger = None