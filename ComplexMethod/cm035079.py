def save_model(
    model,
    optimizer,
    model_path,
    logger,
    config,
    is_best=False,
    prefix="ppocr",
    **kwargs,
):
    """
    save model to the target path
    """
    _mkdir_if_not_exist(model_path, logger)
    model_prefix = os.path.join(model_path, prefix)

    if prefix == "best_accuracy":
        best_model_path = os.path.join(model_path, "best_model")
        _mkdir_if_not_exist(best_model_path, logger)

    paddle.save(optimizer.state_dict(), model_prefix + ".pdopt")
    if prefix == "best_accuracy":
        paddle.save(
            optimizer.state_dict(), os.path.join(best_model_path, "model.pdopt")
        )

    is_nlp_model = config["Architecture"]["model_type"] == "kie" and config[
        "Architecture"
    ]["algorithm"] not in ["SDMGR"]
    if is_nlp_model is not True:
        paddle.save(model.state_dict(), model_prefix + ".pdparams")
        metric_prefix = model_prefix

        if prefix == "best_accuracy":
            paddle.save(
                model.state_dict(), os.path.join(best_model_path, "model.pdparams")
            )

    else:  # for kie system, we follow the save/load rules in NLP
        if config["Global"]["distributed"]:
            arch = model._layers
        else:
            arch = model
        if config["Architecture"]["algorithm"] in ["Distillation"]:
            arch = arch.Student
        arch.backbone.model.save_pretrained(model_prefix)
        metric_prefix = os.path.join(model_prefix, "metric")

        if prefix == "best_accuracy":
            arch.backbone.model.save_pretrained(best_model_path)

    save_model_info = kwargs.pop("save_model_info", False)
    if save_model_info:
        with open(os.path.join(model_path, f"{prefix}.info.json"), "w") as f:
            json.dump(kwargs, f)
        logger.info("Already save model info in {}".format(model_path))
        if prefix != "latest":
            done_flag = kwargs.pop("done_flag", False)
            update_train_results(config, prefix, save_model_info, done_flag=done_flag)

    # save metric and config
    with open(metric_prefix + ".states", "wb") as f:
        pickle.dump(kwargs, f, protocol=2)
    if is_best:
        logger.info("save best model is to {}".format(model_prefix))
    else:
        logger.info("save model in {}".format(model_prefix))