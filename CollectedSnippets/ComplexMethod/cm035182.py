def eval(
    model,
    valid_dataloader,
    post_process_class,
    eval_class,
    model_type=None,
    extra_input=False,
    scaler=None,
    amp_level="O2",
    amp_custom_black_list=[],
    amp_custom_white_list=[],
    amp_dtype="float16",
):
    model.eval()
    with paddle.no_grad():
        total_frame = 0.0
        total_time = 0.0
        pbar = tqdm(
            total=len(valid_dataloader), desc="eval model:", position=0, leave=True
        )
        max_iter = (
            len(valid_dataloader) - 1
            if platform.system() == "Windows"
            else len(valid_dataloader)
        )
        sum_images = 0
        for idx, batch in enumerate(valid_dataloader):
            if idx >= max_iter:
                break
            images = batch[0]
            start = time.time()

            # use amp
            if scaler:
                with paddle.amp.auto_cast(
                    level=amp_level,
                    custom_black_list=amp_custom_black_list,
                    dtype=amp_dtype,
                ):
                    if model_type == "table" or extra_input:
                        preds = model(images, data=batch[1:])
                    elif model_type in ["kie"]:
                        preds = model(batch)
                    elif model_type in ["can"]:
                        preds = model(batch[:3])
                    elif model_type in ["latexocr"]:
                        preds = model(batch)
                    elif model_type in ["sr"]:
                        preds = model(batch)
                        sr_img = preds["sr_img"]
                        lr_img = preds["lr_img"]
                    else:
                        preds = model(images)
                preds = to_float32(preds)
            else:
                if model_type == "table" or extra_input:
                    preds = model(images, data=batch[1:])
                elif model_type in ["kie"]:
                    preds = model(batch)
                elif model_type in ["can"]:
                    preds = model(batch[:3])
                elif model_type in ["latexocr", "unimernet", "pp_formulanet"]:
                    preds = model(batch)
                elif model_type in ["sr"]:
                    preds = model(batch)
                    sr_img = preds["sr_img"]
                    lr_img = preds["lr_img"]
                else:
                    preds = model(images)

            batch_numpy = []
            for item in batch:
                if isinstance(item, paddle.Tensor):
                    batch_numpy.append(item.numpy())
                else:
                    batch_numpy.append(item)
            # Obtain usable results from post-processing methods
            total_time += time.time() - start
            # Evaluate the results of the current batch
            if model_type in ["table", "kie"]:
                if post_process_class is None:
                    eval_class(preds, batch_numpy)
                else:
                    post_result = post_process_class(preds, batch_numpy)
                    eval_class(post_result, batch_numpy)
            elif model_type in ["sr"]:
                eval_class(preds, batch_numpy)
            elif model_type in ["can"]:
                eval_class(preds[0], batch_numpy[2:], epoch_reset=(idx == 0))
            elif model_type in ["latexocr", "unimernet", "pp_formulanet"]:
                post_result = post_process_class(preds, batch[1], "eval")
                eval_class(post_result[0], post_result[1], epoch_reset=(idx == 0))
            else:
                post_result = post_process_class(preds, batch_numpy[1])
                eval_class(post_result, batch_numpy)

            pbar.update(1)
            total_frame += len(images)
            sum_images += 1
        # Get final metric，eg. acc or hmean
        metric = eval_class.get_metric()

    pbar.close()
    model.train()
    # Avoid ZeroDivisionError
    if total_time > 0:
        metric["fps"] = total_frame / total_time
    else:
        metric["fps"] = 0  # or set to a fallback value
    return metric