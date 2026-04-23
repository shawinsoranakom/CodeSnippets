def train(
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
    step_pre_epoch,
    log_writer=None,
    scaler=None,
    amp_level="O2",
    amp_custom_black_list=[],
    amp_custom_white_list=[],
    amp_dtype="float16",
):
    cal_metric_during_train = config["Global"].get("cal_metric_during_train", False)
    calc_epoch_interval = config["Global"].get("calc_epoch_interval", 1)
    log_smooth_window = config["Global"]["log_smooth_window"]
    epoch_num = config["Global"]["epoch_num"]
    print_batch_step = config["Global"]["print_batch_step"]
    eval_batch_step = config["Global"]["eval_batch_step"]
    eval_batch_epoch = config["Global"].get("eval_batch_epoch", None)
    profiler_options = config["profiler_options"]
    print_mem_info = config["Global"].get("print_mem_info", True)
    uniform_output_enabled = config["Global"].get("uniform_output_enabled", False)

    global_step = 0
    if "global_step" in pre_best_model_dict:
        global_step = pre_best_model_dict["global_step"]
    start_eval_step = 0
    if isinstance(eval_batch_step, list) and len(eval_batch_step) >= 2:
        start_eval_step = eval_batch_step[0] if not eval_batch_epoch else 0
        eval_batch_step = (
            eval_batch_step[1]
            if not eval_batch_epoch
            else step_pre_epoch * eval_batch_epoch
        )
        if len(valid_dataloader) == 0:
            logger.info(
                "No Images in eval dataset, evaluation during training "
                "will be disabled"
            )
            start_eval_step = 1e111
        logger.info(
            "During the training process, after the {}th iteration, "
            "an evaluation is run every {} iterations".format(
                start_eval_step, eval_batch_step
            )
        )
    save_epoch_step = config["Global"]["save_epoch_step"]
    save_model_dir = config["Global"]["save_model_dir"]
    if not os.path.exists(save_model_dir):
        os.makedirs(save_model_dir)
    main_indicator = eval_class.main_indicator
    best_model_dict = {main_indicator: 0}
    best_model_dict.update(pre_best_model_dict)
    train_stats = TrainingStats(log_smooth_window, ["lr"])
    model_average = False
    model.train()

    use_srn = config["Architecture"]["algorithm"] == "SRN"
    extra_input_models = [
        "SRN",
        "NRTR",
        "SAR",
        "SEED",
        "SVTR",
        "SVTR_LCNet",
        "SPIN",
        "VisionLAN",
        "RobustScanner",
        "RFL",
        "DRRG",
        "SATRN",
        "SVTR_HGNet",
        "ParseQ",
        "CPPD",
    ]
    extra_input = False
    if config["Architecture"]["algorithm"] == "Distillation":
        for key in config["Architecture"]["Models"]:
            extra_input = (
                extra_input
                or config["Architecture"]["Models"][key]["algorithm"]
                in extra_input_models
            )
    else:
        extra_input = config["Architecture"]["algorithm"] in extra_input_models
    try:
        model_type = config["Architecture"]["model_type"]
    except:
        model_type = None

    algorithm = config["Architecture"]["algorithm"]

    start_epoch = (
        best_model_dict["start_epoch"] if "start_epoch" in best_model_dict else 1
    )

    total_samples = 0
    train_reader_cost = 0.0
    train_batch_cost = 0.0
    reader_start = time.time()
    eta_meter = AverageMeter()

    max_iter = (
        len(train_dataloader) - 1
        if platform.system() == "Windows"
        else len(train_dataloader)
    )

    for epoch in range(start_epoch, epoch_num + 1):
        if train_dataloader.dataset.need_reset:
            train_dataloader = build_dataloader(
                config, "Train", device, logger, seed=epoch
            )
            max_iter = (
                len(train_dataloader) - 1
                if platform.system() == "Windows"
                else len(train_dataloader)
            )

        for idx, batch in enumerate(train_dataloader):
            model.train()
            profiler.add_profiler_step(profiler_options)
            train_reader_cost += time.time() - reader_start
            if idx >= max_iter:
                break
            lr = optimizer.get_lr()
            images = batch[0]
            if use_srn:
                model_average = True
            # use amp
            if scaler:
                with paddle.amp.auto_cast(
                    level=amp_level,
                    custom_black_list=amp_custom_black_list,
                    custom_white_list=amp_custom_white_list,
                    dtype=amp_dtype,
                ):
                    if model_type == "table" or extra_input:
                        preds = model(images, data=batch[1:])
                    elif model_type in ["kie"]:
                        preds = model(batch)
                    elif algorithm in ["CAN"]:
                        preds = model(batch[:3])
                    elif algorithm in [
                        "LaTeXOCR",
                        "UniMERNet",
                        "PP-FormulaNet-S",
                        "PP-FormulaNet-L",
                        "PP-FormulaNet_plus-S",
                        "PP-FormulaNet_plus-M",
                        "PP-FormulaNet_plus-L",
                    ]:
                        preds = model(batch)
                    else:
                        preds = model(images)
                preds = to_float32(preds)
                loss = loss_class(preds, batch)
                avg_loss = loss["loss"]
                scaled_avg_loss = scaler.scale(avg_loss)
                scaled_avg_loss.backward()
                scaler.minimize(optimizer, scaled_avg_loss)
            else:
                if model_type == "table" or extra_input:
                    preds = model(images, data=batch[1:])
                elif model_type in ["kie", "sr"]:
                    preds = model(batch)
                elif algorithm in ["CAN"]:
                    preds = model(batch[:3])
                elif algorithm in [
                    "LaTeXOCR",
                    "UniMERNet",
                    "PP-FormulaNet-S",
                    "PP-FormulaNet-L",
                    "PP-FormulaNet_plus-S",
                    "PP-FormulaNet_plus-M",
                    "PP-FormulaNet_plus-L",
                ]:
                    preds = model(batch)
                else:
                    preds = model(images)
                loss = loss_class(preds, batch)
                avg_loss = loss["loss"]
                avg_loss.backward()
                optimizer.step()

            optimizer.clear_grad()

            if (
                cal_metric_during_train and epoch % calc_epoch_interval == 0
            ):  # only rec and cls need
                batch = [item.numpy() for item in batch]
                if model_type in ["kie", "sr"]:
                    eval_class(preds, batch)
                elif model_type in ["table"]:
                    post_result = post_process_class(preds, batch)
                    eval_class(post_result, batch)
                elif algorithm in ["CAN"]:
                    model_type = "can"
                    eval_class(preds[0], batch[2:], epoch_reset=(idx == 0))
                elif algorithm in ["LaTeXOCR"]:
                    model_type = "latexocr"
                    post_result = post_process_class(preds, batch[1], mode="train")
                    eval_class(post_result[0], post_result[1], epoch_reset=(idx == 0))
                elif algorithm in ["UniMERNet"]:
                    model_type = "unimernet"
                    post_result = post_process_class(preds[0], batch[1], mode="train")
                    eval_class(post_result[0], post_result[1], epoch_reset=(idx == 0))
                elif algorithm in [
                    "PP-FormulaNet-S",
                    "PP-FormulaNet-L",
                    "PP-FormulaNet_plus-S",
                    "PP-FormulaNet_plus-M",
                    "PP-FormulaNet_plus-L",
                ]:
                    model_type = "pp_formulanet"
                    post_result = post_process_class(preds[0], batch[1], mode="train")
                    eval_class(post_result[0], post_result[1], epoch_reset=(idx == 0))
                else:
                    if config["Loss"]["name"] in [
                        "MultiLoss",
                        "MultiLoss_v2",
                    ]:  # for multi head loss
                        post_result = post_process_class(
                            preds["ctc"], batch[1]
                        )  # for CTC head out
                    elif config["Loss"]["name"] in ["VLLoss"]:
                        post_result = post_process_class(preds, batch[1], batch[-1])
                    else:
                        post_result = post_process_class(preds, batch[1])
                    eval_class(post_result, batch)
                metric = eval_class.get_metric()
                train_stats.update(metric)

            train_batch_time = time.time() - reader_start
            train_batch_cost += train_batch_time
            eta_meter.update(train_batch_time)
            global_step += 1
            total_samples += len(images)

            if not isinstance(lr_scheduler, float):
                lr_scheduler.step()

            # logger and visualdl
            stats = {
                k: float(v) if v.shape == [] else v.numpy().mean()
                for k, v in loss.items()
            }
            stats["lr"] = lr
            train_stats.update(stats)

            if log_writer is not None and dist.get_rank() == 0:
                log_writer.log_metrics(
                    metrics=train_stats.get(), prefix="TRAIN", step=global_step
                )

            if (global_step > 0 and global_step % print_batch_step == 0) or (
                idx >= len(train_dataloader) - 1
            ):
                logs = train_stats.log()

                eta_sec = (
                    (epoch_num + 1 - epoch) * len(train_dataloader) - idx - 1
                ) * eta_meter.avg
                eta_sec_format = str(datetime.timedelta(seconds=int(eta_sec)))
                max_mem_reserved_str = ""
                max_mem_allocated_str = ""
                if paddle.device.is_compiled_with_cuda() and print_mem_info:
                    max_mem_reserved_str = f", max_mem_reserved: {paddle.device.cuda.max_memory_reserved() // (1024 ** 2)} MB,"
                    max_mem_allocated_str = f" max_mem_allocated: {paddle.device.cuda.max_memory_allocated() // (1024 ** 2)} MB"
                strs = (
                    "epoch: [{}/{}], global_step: {}, {}, avg_reader_cost: "
                    "{:.5f} s, avg_batch_cost: {:.5f} s, avg_samples: {}, "
                    "ips: {:.5f} samples/s, eta: {}{}{}".format(
                        epoch,
                        epoch_num,
                        global_step,
                        logs,
                        train_reader_cost / print_batch_step,
                        train_batch_cost / print_batch_step,
                        total_samples / print_batch_step,
                        total_samples / train_batch_cost,
                        eta_sec_format,
                        max_mem_reserved_str,
                        max_mem_allocated_str,
                    )
                )
                logger.info(strs)

                total_samples = 0
                train_reader_cost = 0.0
                train_batch_cost = 0.0
            # eval
            if (
                global_step > start_eval_step
                and (global_step - start_eval_step) % eval_batch_step == 0
                and dist.get_rank() == 0
            ):
                if model_average:
                    Model_Average = paddle.incubate.ModelAverage(
                        0.15,
                        parameters=model.parameters(),
                        min_average_window=10000,
                        max_average_window=15625,
                    )
                    Model_Average.apply()
                cur_metric = eval(
                    model,
                    valid_dataloader,
                    post_process_class,
                    eval_class,
                    model_type,
                    extra_input=extra_input,
                    scaler=scaler,
                    amp_level=amp_level,
                    amp_custom_black_list=amp_custom_black_list,
                    amp_custom_white_list=amp_custom_white_list,
                    amp_dtype=amp_dtype,
                )
                cur_metric_str = "cur metric, {}".format(
                    ", ".join(["{}: {}".format(k, v) for k, v in cur_metric.items()])
                )
                logger.info(cur_metric_str)

                # logger metric
                if log_writer is not None:
                    log_writer.log_metrics(
                        metrics=cur_metric, prefix="EVAL", step=global_step
                    )

                if cur_metric[main_indicator] >= best_model_dict[main_indicator]:
                    best_model_dict.update(cur_metric)
                    best_model_dict["best_epoch"] = epoch
                    prefix = "best_accuracy"
                    if uniform_output_enabled:
                        export(
                            config,
                            model,
                            os.path.join(save_model_dir, prefix, "inference"),
                        )
                        gc.collect()
                        model_info = {"epoch": epoch, "metric": best_model_dict}
                    else:
                        model_info = None
                    save_model(
                        model,
                        optimizer,
                        (
                            os.path.join(save_model_dir, prefix)
                            if uniform_output_enabled
                            else save_model_dir
                        ),
                        logger,
                        config,
                        is_best=True,
                        prefix=prefix,
                        save_model_info=model_info,
                        best_model_dict=best_model_dict,
                        epoch=epoch,
                        global_step=global_step,
                    )
                best_str = "best metric, {}".format(
                    ", ".join(
                        ["{}: {}".format(k, v) for k, v in best_model_dict.items()]
                    )
                )
                logger.info(best_str)
                # logger best metric
                if log_writer is not None:
                    log_writer.log_metrics(
                        metrics={
                            "best_{}".format(main_indicator): best_model_dict[
                                main_indicator
                            ]
                        },
                        prefix="EVAL",
                        step=global_step,
                    )

                    log_writer.log_model(
                        is_best=True, prefix="best_accuracy", metadata=best_model_dict
                    )

            reader_start = time.time()
        if dist.get_rank() == 0:
            prefix = "latest"
            if uniform_output_enabled:
                export(config, model, os.path.join(save_model_dir, prefix, "inference"))
                gc.collect()
                model_info = {"epoch": epoch, "metric": best_model_dict}
            else:
                model_info = None
            save_model(
                model,
                optimizer,
                (
                    os.path.join(save_model_dir, prefix)
                    if uniform_output_enabled
                    else save_model_dir
                ),
                logger,
                config,
                is_best=False,
                prefix=prefix,
                save_model_info=model_info,
                best_model_dict=best_model_dict,
                epoch=epoch,
                global_step=global_step,
            )

            if log_writer is not None:
                log_writer.log_model(is_best=False, prefix="latest")

        if dist.get_rank() == 0 and epoch > 0 and epoch % save_epoch_step == 0:
            prefix = "iter_epoch_{}".format(epoch)
            if uniform_output_enabled:
                export(config, model, os.path.join(save_model_dir, prefix, "inference"))
                gc.collect()
                model_info = {"epoch": epoch, "metric": best_model_dict}
            else:
                model_info = None
            save_model(
                model,
                optimizer,
                (
                    os.path.join(save_model_dir, prefix)
                    if uniform_output_enabled
                    else save_model_dir
                ),
                logger,
                config,
                is_best=False,
                prefix=prefix,
                save_model_info=model_info,
                best_model_dict=best_model_dict,
                epoch=epoch,
                global_step=global_step,
                done_flag=epoch == config["Global"]["epoch_num"],
            )
            if log_writer is not None:
                log_writer.log_model(
                    is_best=False, prefix="iter_epoch_{}".format(epoch)
                )

    best_str = "best metric, {}".format(
        ", ".join(["{}: {}".format(k, v) for k, v in best_model_dict.items()])
    )
    logger.info(best_str)
    if dist.get_rank() == 0 and log_writer is not None:
        log_writer.close()
    return