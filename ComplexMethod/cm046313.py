def __init__(self, cfg=DEFAULT_CFG, overrides=None, _callbacks: dict | None = None):
        """Initialize the BaseTrainer class.

        Args:
            cfg (str | dict | SimpleNamespace, optional): Path to a configuration file or configuration object.
            overrides (dict, optional): Configuration overrides.
            _callbacks (dict, optional): Dictionary of callback functions.
        """
        self.hub_session = overrides.pop("session", None)  # HUB
        self.args = get_cfg(cfg, overrides)
        self.check_resume(overrides)
        self.device = select_device(self.args.device)
        # Update "-1" devices so post-training val does not repeat search
        self.args.device = os.getenv("CUDA_VISIBLE_DEVICES") if "cuda" in str(self.device) else str(self.device)
        self.validator = None
        self.metrics = None
        self.plots = {}
        init_seeds(self.args.seed + 1 + RANK, deterministic=self.args.deterministic)

        # Dirs
        self.save_dir = get_save_dir(self.args)
        self.args.name = self.save_dir.name  # update name for loggers
        self.wdir = self.save_dir / "weights"  # weights dir
        if RANK in {-1, 0}:
            self.wdir.mkdir(parents=True, exist_ok=True)  # make dir
            self.args.save_dir = str(self.save_dir)
            # Save run args, serializing augmentations as reprs for resume compatibility
            args_dict = vars(self.args).copy()
            if args_dict.get("augmentations") is not None:
                # Serialize Albumentations transforms as their repr strings for checkpoint compatibility
                args_dict["augmentations"] = [repr(t) for t in args_dict["augmentations"]]
            YAML.save(self.save_dir / "args.yaml", args_dict)  # save run args
        self.last, self.best = self.wdir / "last.pt", self.wdir / "best.pt"  # checkpoint paths
        self.save_period = self.args.save_period

        self.batch_size = self.args.batch
        self.epochs = self.args.epochs or 100  # in case users accidentally pass epochs=None with timed training
        self.start_epoch = 0
        if RANK == -1:
            print_args(vars(self.args))

        # Device
        if self.device.type in {"cpu", "mps"}:
            self.args.workers = 0  # faster CPU training as time dominated by inference, not dataloading

        # Callbacks - initialize early so on_pretrain_routine_start can capture original args.data
        self.callbacks = _callbacks or callbacks.get_default_callbacks()

        if isinstance(self.args.device, str) and len(self.args.device):  # i.e. device='0' or device='0,1,2,3'
            world_size = len(self.args.device.split(","))
        elif isinstance(self.args.device, (tuple, list)):  # i.e. device=[0, 1, 2, 3] (multi-GPU from CLI is list)
            world_size = len(self.args.device)
        elif self.args.device in {"cpu", "mps"}:  # i.e. device='cpu' or 'mps'
            world_size = 0
        elif torch.cuda.is_available():  # i.e. device=None or device='' or device=number
            world_size = 1  # default to device 0
        else:  # i.e. device=None or device=''
            world_size = 0

        self.ddp = world_size > 1 and "LOCAL_RANK" not in os.environ
        self.world_size = world_size
        # Run on_pretrain_routine_start before get_dataset() to capture original args.data (e.g., ul:// URIs)
        if RANK in {-1, 0} and not self.ddp:
            callbacks.add_integration_callbacks(self)
            self.run_callbacks("on_pretrain_routine_start")

        # Model and Dataset
        self.model = check_model_file_from_stem(self.args.model)  # add suffix, i.e. yolo26n -> yolo26n.pt
        with torch_distributed_zero_first(LOCAL_RANK):  # avoid auto-downloading dataset multiple times
            self.data = self.get_dataset()

        self.ema = None

        # Optimization utils init
        self.lf = None
        self.scheduler = None

        # Epoch level metrics
        self.best_fitness = None
        self.fitness = None
        self.loss = None
        self.tloss = None
        self.loss_names = ["Loss"]
        self.csv = self.save_dir / "results.csv"
        if self.csv.exists() and not self.args.resume:
            self.csv.unlink()
        self.plot_idx = [0, 1, 2]
        self.nan_recovery_attempts = 0