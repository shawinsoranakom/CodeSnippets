def preprocess(is_train=False):
    FLAGS = ArgsParser().parse_args()
    profiler_options = FLAGS.profiler_options
    config = load_config(FLAGS.config)
    config = merge_config(config, FLAGS.opt)
    profile_dic = {"profiler_options": FLAGS.profiler_options}
    config = merge_config(config, profile_dic)

    if is_train:
        # save_config
        save_model_dir = config["Global"]["save_model_dir"]
        os.makedirs(save_model_dir, exist_ok=True)
        with open(os.path.join(save_model_dir, "config.yml"), "w") as f:
            yaml.dump(dict(config), f, default_flow_style=False, sort_keys=False)
        log_file = "{}/train.log".format(save_model_dir)
    else:
        log_file = None

    log_ranks = config["Global"].get("log_ranks", "0")
    logger = get_logger(log_file=log_file, log_ranks=log_ranks)

    # check if set use_gpu=True in paddlepaddle cpu version
    use_gpu = config["Global"].get("use_gpu", False)
    use_xpu = config["Global"].get("use_xpu", False)
    use_npu = config["Global"].get("use_npu", False)
    use_mlu = config["Global"].get("use_mlu", False)
    use_gcu = config["Global"].get("use_gcu", False)
    use_metax_gpu = config["Global"].get("use_metax_gpu", False)

    use_iluvatar_gpu = config["Global"].get("use_iluvatar_gpu", False)

    alg = config["Architecture"]["algorithm"]
    assert alg in [
        "EAST",
        "DB",
        "SAST",
        "Rosetta",
        "CRNN",
        "STARNet",
        "RARE",
        "SRN",
        "CLS",
        "PGNet",
        "Distillation",
        "NRTR",
        "TableAttn",
        "SAR",
        "PSE",
        "SEED",
        "SDMGR",
        "LayoutXLM",
        "LayoutLM",
        "LayoutLMv2",
        "PREN",
        "FCE",
        "SVTR",
        "SVTR_LCNet",
        "ViTSTR",
        "ABINet",
        "DB++",
        "TableMaster",
        "SPIN",
        "VisionLAN",
        "Gestalt",
        "SLANet",
        "RobustScanner",
        "CT",
        "RFL",
        "DRRG",
        "CAN",
        "Telescope",
        "SATRN",
        "SVTR_HGNet",
        "ParseQ",
        "CPPD",
        "LaTeXOCR",
        "UniMERNet",
        "SLANeXt",
        "PP-FormulaNet-S",
        "PP-FormulaNet-L",
        "PP-FormulaNet_plus-S",
        "PP-FormulaNet_plus-M",
        "PP-FormulaNet_plus-L",
    ]

    if use_xpu:
        device = "xpu:{0}".format(os.getenv("FLAGS_selected_xpus", 0))
    elif use_npu:
        device = "npu:{0}".format(os.getenv("FLAGS_selected_npus", 0))
    elif use_mlu:
        device = "mlu:{0}".format(os.getenv("FLAGS_selected_mlus", 0))
    elif use_gcu:  # Use Enflame GCU(General Compute Unit)
        device = "gcu:{0}".format(os.getenv("FLAGS_selected_gcus", 0))
    elif use_metax_gpu:  # Use Enflame GCU(General Compute Unit)
        device = "metax:{0}".format(os.getenv("FLAGS_selected_metaxs", 0))
    elif use_iluvatar_gpu:
        device = "iluvatar_gpu:{0}".format(dist.ParallelEnv().dev_id)
    else:
        device = "gpu:{}".format(dist.ParallelEnv().dev_id) if use_gpu else "cpu"
    check_device(
        use_gpu, use_xpu, use_npu, use_mlu, use_gcu, use_iluvatar_gpu, use_metax_gpu
    )

    device = paddle.set_device(device)

    config["Global"]["distributed"] = dist.get_world_size() != 1

    loggers = []

    if "use_visualdl" in config["Global"] and config["Global"]["use_visualdl"]:
        logger.warning(
            "You are using VisualDL, the VisualDL is deprecated and "
            "removed in ppocr!"
        )
        log_writer = None
    if (
        "use_wandb" in config["Global"] and config["Global"]["use_wandb"]
    ) or "wandb" in config:
        save_dir = config["Global"]["save_model_dir"]
        wandb_writer_path = "{}/wandb".format(save_dir)
        if "wandb" in config:
            wandb_params = config["wandb"]
        else:
            wandb_params = dict()
        wandb_params.update({"save_dir": save_dir})
        log_writer = WandbLogger(**wandb_params, config=config)
        loggers.append(log_writer)
    else:
        log_writer = None
    print_dict(config, logger)

    if loggers:
        log_writer = Loggers(loggers)
    else:
        log_writer = None

    logger.info("train with paddle {} and device {}".format(paddle.__version__, device))
    return config, device, logger, log_writer