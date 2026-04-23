def main(config, device, logger, vdl_writer):
    # init dist environment
    if config["Global"]["distributed"]:
        dist.init_parallel_env()

    global_config = config["Global"]

    # build dataloader
    set_signal_handlers()
    train_dataloader = build_dataloader(config, "Train", device, logger)
    if config["Eval"]:
        valid_dataloader = build_dataloader(config, "Eval", device, logger)
    else:
        valid_dataloader = None

    # build post process
    post_process_class = build_post_process(config["PostProcess"], global_config)

    # build model
    # for rec algorithm
    if hasattr(post_process_class, "character"):
        char_num = len(getattr(post_process_class, "character"))
        if config["Architecture"]["algorithm"] in [
            "Distillation",
        ]:  # distillation model
            for key in config["Architecture"]["Models"]:
                if (
                    config["Architecture"]["Models"][key]["Head"]["name"] == "MultiHead"
                ):  # for multi head
                    if config["PostProcess"]["name"] == "DistillationSARLabelDecode":
                        char_num = char_num - 2
                    # update SARLoss params
                    assert (
                        list(config["Loss"]["loss_config_list"][-1].keys())[0]
                        == "DistillationSARLoss"
                    )
                    config["Loss"]["loss_config_list"][-1]["DistillationSARLoss"][
                        "ignore_index"
                    ] = (char_num + 1)
                    out_channels_list = {}
                    out_channels_list["CTCLabelDecode"] = char_num
                    out_channels_list["SARLabelDecode"] = char_num + 2
                    config["Architecture"]["Models"][key]["Head"][
                        "out_channels_list"
                    ] = out_channels_list
                else:
                    config["Architecture"]["Models"][key]["Head"][
                        "out_channels"
                    ] = char_num
        elif config["Architecture"]["Head"]["name"] == "MultiHead":  # for multi head
            if config["PostProcess"]["name"] == "SARLabelDecode":
                char_num = char_num - 2
            # update SARLoss params
            assert list(config["Loss"]["loss_config_list"][1].keys())[0] == "SARLoss"
            if config["Loss"]["loss_config_list"][1]["SARLoss"] is None:
                config["Loss"]["loss_config_list"][1]["SARLoss"] = {
                    "ignore_index": char_num + 1
                }
            else:
                config["Loss"]["loss_config_list"][1]["SARLoss"]["ignore_index"] = (
                    char_num + 1
                )
            out_channels_list = {}
            out_channels_list["CTCLabelDecode"] = char_num
            out_channels_list["SARLabelDecode"] = char_num + 2
            config["Architecture"]["Head"]["out_channels_list"] = out_channels_list
        else:  # base rec model
            config["Architecture"]["Head"]["out_channels"] = char_num

        if config["PostProcess"]["name"] == "SARLabelDecode":  # for SAR model
            config["Loss"]["ignore_index"] = char_num - 1
    model = build_model(config["Architecture"])

    pre_best_model_dict = dict()
    # load fp32 model to begin quantization
    pre_best_model_dict = load_model(
        config, model, None, config["Architecture"]["model_type"]
    )

    freeze_params = False
    if config["Architecture"]["algorithm"] in ["Distillation"]:
        for key in config["Architecture"]["Models"]:
            freeze_params = freeze_params or config["Architecture"]["Models"][key].get(
                "freeze_params", False
            )
    act = None if freeze_params else PACT
    quanter = QAT(config=quant_config, act_preprocess=act)
    quanter.quantize(model)

    if config["Global"]["distributed"]:
        model = paddle.DataParallel(model)

    # build loss
    loss_class = build_loss(config["Loss"])

    # build optim
    optimizer, lr_scheduler = build_optimizer(
        config["Optimizer"],
        epochs=config["Global"]["epoch_num"],
        step_each_epoch=len(train_dataloader),
        model=model,
    )

    # resume PACT training process
    pre_best_model_dict = load_model(
        config, model, optimizer, config["Architecture"]["model_type"]
    )

    # build metric
    eval_class = build_metric(config["Metric"])

    logger.info(
        "train dataloader has {} iters, valid dataloader has {} iters".format(
            len(train_dataloader), len(valid_dataloader)
        )
    )

    # start train
    program.train(
        config,
        train_dataloader,
        valid_dataloader,
        device,
        model,
        loss_class,
        optimizer,
        lr_scheduler,
        post_process_class,
        eval_class,
        pre_best_model_dict,
        logger,
        vdl_writer,
    )