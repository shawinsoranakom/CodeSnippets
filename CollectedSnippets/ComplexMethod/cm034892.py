def main(config, device, logger, vdl_writer):
    # init dist environment
    if config["Global"]["distributed"]:
        dist.init_parallel_env()

    global_config = config["Global"]

    # build dataloader
    set_signal_handlers()
    config["Train"]["loader"]["num_workers"] = 0
    is_layoutxlm_ser = (
        config["Architecture"]["model_type"] == "kie"
        and config["Architecture"]["Backbone"]["name"] == "LayoutXLMForSer"
    )
    train_dataloader = build_dataloader(config, "Train", device, logger)
    if config["Eval"]:
        config["Eval"]["loader"]["num_workers"] = 0
        valid_dataloader = build_dataloader(config, "Eval", device, logger)
        if is_layoutxlm_ser:
            train_dataloader = valid_dataloader
    else:
        valid_dataloader = None

    paddle.enable_static()
    exe = paddle.static.Executor(device)

    if "inference_model" in global_config.keys():  # , 'inference_model'):
        inference_model_dir = global_config["inference_model"]
    else:
        inference_model_dir = os.path.dirname(global_config["pretrained_model"])
        if not (
            os.path.exists(os.path.join(inference_model_dir, "inference.pdmodel"))
            and os.path.exists(os.path.join(inference_model_dir, "inference.pdiparams"))
        ):
            raise ValueError(
                "Please set inference model dir in Global.inference_model or Global.pretrained_model for post-quantization"
            )

    if is_layoutxlm_ser:
        generator = sample_generator_layoutxlm_ser(train_dataloader)
    else:
        generator = sample_generator(train_dataloader)

    paddleslim.quant.quant_post_static(
        executor=exe,
        model_dir=inference_model_dir,
        model_filename="inference.pdmodel",
        params_filename="inference.pdiparams",
        quantize_model_path=global_config["save_inference_dir"],
        sample_generator=generator,
        save_model_filename="inference.pdmodel",
        save_params_filename="inference.pdiparams",
        batch_size=1,
        batch_nums=None,
    )