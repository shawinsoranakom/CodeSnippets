def train_distill_multiopt(config, scaler=None):
    EPOCH = config["epoch"]
    topk = config["topk"]

    batch_size = config["TRAIN"]["batch_size"]
    num_workers = config["TRAIN"]["num_workers"]
    train_loader = build_dataloader(
        "train", batch_size=batch_size, num_workers=num_workers
    )

    # build metric
    metric_func = create_metric

    # model = distillmv3_large_x0_5(class_dim=100)
    model = build_model(config)

    # build_optimizer
    optimizer, lr_scheduler = create_optimizer(
        config, parameter_list=model.student.parameters()
    )
    optimizer1, lr_scheduler1 = create_optimizer(
        config, parameter_list=model.student1.parameters()
    )

    # load model
    pre_best_model_dict = load_model(config, model, optimizer)
    if len(pre_best_model_dict) > 0:
        pre_str = "The metric of loaded metric as follows {}".format(
            ", ".join(["{}: {}".format(k, v) for k, v in pre_best_model_dict.items()])
        )
        logger.info(pre_str)

    # quant train
    if "quant_train" in config and config["quant_train"] is True:
        quanter = QAT(config=quant_config, act_preprocess=PACT)
        quanter.quantize(model)
    elif "prune_train" in config and config["prune_train"] is True:
        model = prune_model(model, [1, 3, 32, 32], 0.1)
    else:
        pass

    model.train()

    model = paddle.DataParallel(model)

    # build loss function
    loss_func_distill = LossDistill(model_name_list=["student", "student1"])
    loss_func_dml = DMLLoss(model_name_pairs=["student", "student1"])
    loss_func_js = KLJSLoss(mode="js")

    data_num = len(train_loader)
    best_acc = {}
    for epoch in range(EPOCH):
        st = time.time()
        for idx, data in enumerate(train_loader):
            img_batch, label = data
            img_batch = paddle.transpose(img_batch, [0, 3, 1, 2])
            label = paddle.unsqueeze(label, -1)

            if scaler is not None:
                with paddle.amp.auto_cast():
                    outs = model(img_batch)
            else:
                outs = model(img_batch)

            # cal metric
            acc = metric_func(outs["student"], label)

            # cal loss
            avg_loss = (
                loss_func_distill(outs, label)["student"]
                + loss_func_dml(outs, label)["student_student1"]
            )
            avg_loss1 = (
                loss_func_distill(outs, label)["student1"]
                + loss_func_dml(outs, label)["student_student1"]
            )

            if scaler is None:
                # backward
                avg_loss.backward(retain_graph=True)
                optimizer.step()
                optimizer.clear_grad()

                avg_loss1.backward()
                optimizer1.step()
                optimizer1.clear_grad()
            else:
                scaled_avg_loss = scaler.scale(avg_loss)
                scaled_avg_loss.backward()
                scaler.minimize(optimizer, scaled_avg_loss)

                scaled_avg_loss = scaler.scale(avg_loss1)
                scaled_avg_loss.backward()
                scaler.minimize(optimizer1, scaled_avg_loss)

            if not isinstance(lr_scheduler, float):
                lr_scheduler.step()
            if not isinstance(lr_scheduler1, float):
                lr_scheduler1.step()

            if idx % 10 == 0:
                et = time.time()
                strs = f"epoch: [{epoch}/{EPOCH}], iter: [{idx}/{data_num}], "
                strs += f"loss: {float(avg_loss)}, loss1: {float(avg_loss1)}"
                strs += (
                    f", acc_topk1: {float(acc['top1'])}, acc_top5: {float(acc['top5'])}"
                )
                strs += f", batch_time: {round(et-st, 4)} s"
                logger.info(strs)
                st = time.time()

        if epoch % 10 == 0:
            acc = eval(config, model._layers.student)
            if len(best_acc) < 1 or float(acc["top5"]) > best_acc["top5"]:
                best_acc = acc
                best_acc["epoch"] = epoch
                is_best = True
            else:
                is_best = False
            logger.info(
                f"The best acc: acc_topk1: {float(best_acc['top1'])}, acc_top5: {float(best_acc['top5'])}, best_epoch: {best_acc['epoch']}"
            )
            save_model(
                model,
                [optimizer, optimizer1],
                config["save_model_dir"],
                logger,
                is_best,
                prefix="cls_distill_multiopt",
            )