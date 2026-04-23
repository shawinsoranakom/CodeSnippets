def __init__(
        self,
        config,
        model,
        criterion,
        train_loader,
        validate_loader,
        metric_cls,
        post_process=None,
    ):
        config["trainer"]["output_dir"] = os.path.join(
            str(pathlib.Path(os.path.abspath(__name__)).parent),
            config["trainer"]["output_dir"],
        )
        config["name"] = config["name"] + "_" + model.name
        self.save_dir = config["trainer"]["output_dir"]
        self.checkpoint_dir = os.path.join(self.save_dir, "checkpoint")

        os.makedirs(self.checkpoint_dir, exist_ok=True)

        self.global_step = 0
        self.start_epoch = 0
        self.config = config
        self.criterion = criterion
        # logger and tensorboard
        self.visualdl_enable = self.config["trainer"].get("visual_dl", False)
        self.epochs = self.config["trainer"]["epochs"]
        self.log_iter = self.config["trainer"]["log_iter"]
        if paddle.distributed.get_rank() == 0:
            anyconfig.dump(config, os.path.join(self.save_dir, "config.yaml"))
            self.logger = setup_logger(os.path.join(self.save_dir, "train.log"))
            self.logger_info(pformat(self.config))

        self.model = self.apply_to_static(model)

        # device
        if (
            paddle.device.cuda.device_count() > 0
            and paddle.device.is_compiled_with_cuda()
        ):
            self.with_cuda = True
            random.seed(self.config["trainer"]["seed"])
            np.random.seed(self.config["trainer"]["seed"])
            paddle.seed(self.config["trainer"]["seed"])
        else:
            self.with_cuda = False
        self.logger_info("train with and paddle {}".format(paddle.__version__))
        # metrics
        self.metrics = {
            "recall": 0,
            "precision": 0,
            "hmean": 0,
            "train_loss": float("inf"),
            "best_model_epoch": 0,
        }

        self.train_loader = train_loader
        if validate_loader is not None:
            assert post_process is not None and metric_cls is not None
        self.validate_loader = validate_loader
        self.post_process = post_process
        self.metric_cls = metric_cls
        self.train_loader_len = len(train_loader)

        if self.validate_loader is not None:
            self.logger_info(
                "train dataset has {} samples,{} in dataloader, validate dataset has {} samples,{} in dataloader".format(
                    len(self.train_loader.dataset),
                    self.train_loader_len,
                    len(self.validate_loader.dataset),
                    len(self.validate_loader),
                )
            )
        else:
            self.logger_info(
                "train dataset has {} samples,{} in dataloader".format(
                    len(self.train_loader.dataset), self.train_loader_len
                )
            )

        self._initialize_scheduler()

        self._initialize_optimizer()

        # resume or finetune
        if self.config["trainer"]["resume_checkpoint"] != "":
            self._load_checkpoint(
                self.config["trainer"]["resume_checkpoint"], resume=True
            )
        elif self.config["trainer"]["finetune_checkpoint"] != "":
            self._load_checkpoint(
                self.config["trainer"]["finetune_checkpoint"], resume=False
            )

        if self.visualdl_enable and paddle.distributed.get_rank() == 0:
            from visualdl import LogWriter

            self.writer = LogWriter(self.save_dir)

        # 混合精度训练
        self.amp = self.config.get("amp", None)
        if self.amp == "None":
            self.amp = None
        if self.amp:
            self.amp["scaler"] = paddle.amp.GradScaler(
                init_loss_scaling=self.amp.get("scale_loss", 1024),
                use_dynamic_loss_scaling=self.amp.get("use_dynamic_loss_scaling", True),
            )
            self.model, self.optimizer = paddle.amp.decorate(
                models=self.model,
                optimizers=self.optimizer,
                level=self.amp.get("amp_level", "O2"),
            )

        # 分布式训练
        if paddle.device.cuda.device_count() > 1:
            self.model = paddle.DataParallel(self.model)
        # make inverse Normalize
        self.UN_Normalize = False
        for t in self.config["dataset"]["train"]["dataset"]["args"]["transforms"]:
            if t["type"] == "Normalize":
                self.normalize_mean = t["args"]["mean"]
                self.normalize_std = t["args"]["std"]
                self.UN_Normalize = True