def eval_function(exe, compiled_test_program, test_feed_names, test_fetch_list):
    post_process_class = build_post_process(all_config["PostProcess"], global_config)
    eval_class = build_metric(all_config["Metric"])
    model_type = global_config["model_type"]

    with tqdm(
        total=len(val_loader),
        bar_format="Evaluation stage, Run batch:|{bar}| {n_fmt}/{total_fmt}",
        ncols=80,
    ) as t:
        for batch_id, batch in enumerate(val_loader):
            images = batch[0]

            try:
                (preds,) = exe.run(
                    compiled_test_program,
                    feed={test_feed_names[0]: images},
                    fetch_list=test_fetch_list,
                )
            except:
                preds, _ = exe.run(
                    compiled_test_program,
                    feed={test_feed_names[0]: images},
                    fetch_list=test_fetch_list,
                )

            batch_numpy = []
            for item in batch:
                batch_numpy.append(np.array(item))

            if model_type == "det":
                preds_map = {"maps": preds}
                post_result = post_process_class(preds_map, batch_numpy[1])
                eval_class(post_result, batch_numpy)
            elif model_type == "rec":
                post_result = post_process_class(preds, batch_numpy[1])
                eval_class(post_result, batch_numpy)
            t.update()
        metric = eval_class.get_metric()
    logger.info("metric eval ***************")
    for k, v in metric.items():
        logger.info("{}:{}".format(k, v))

    if model_type == "det":
        return metric["hmean"]
    elif model_type == "rec":
        return metric["acc"]
    return metric