def eval(args):
    """
    eval mIoU func
    """
    # DataLoader need run on cpu
    paddle.set_device("cpu")
    devices = paddle.device.get_device().split(":")[0]

    val_loader = build_dataloader(all_config, "Eval", devices, logger)
    post_process_class = build_post_process(all_config["PostProcess"], global_config)
    eval_class = build_metric(all_config["Metric"])
    model_type = global_config["model_type"]

    predictor, rerun_flag = load_predictor(args)

    if rerun_flag:
        eval_dataset = find_images_with_bounding_size(val_loader.dataset)
        batch_sampler = paddle.io.BatchSampler(
            eval_dataset, batch_size=1, shuffle=False, drop_last=False
        )
        val_loader = paddle.io.DataLoader(
            eval_dataset, batch_sampler=batch_sampler, num_workers=4, return_list=True
        )

    input_names = predictor.get_input_names()
    input_handle = predictor.get_input_handle(input_names[0])
    output_names = predictor.get_output_names()
    output_handle = predictor.get_output_handle(output_names[0])
    sample_nums = len(val_loader)
    predict_time = 0.0
    time_min = float("inf")
    time_max = float("-inf")
    print("Start evaluating ( total_iters: {}).".format(sample_nums))

    for batch_id, batch in enumerate(val_loader):
        images = np.array(batch[0])

        batch_numpy = []
        for item in batch:
            batch_numpy.append(np.array(item))

        # ori_shape = np.array(batch_numpy).shape[-2:]
        input_handle.reshape(images.shape)
        input_handle.copy_from_cpu(images)
        start_time = time.time()

        predictor.run()
        preds = output_handle.copy_to_cpu()

        end_time = time.time()
        timed = end_time - start_time
        time_min = min(time_min, timed)
        time_max = max(time_max, timed)
        predict_time += timed

        if model_type == "det":
            preds_map = {"maps": preds}
            post_result = post_process_class(preds_map, batch_numpy[1])
            eval_class(post_result, batch_numpy)
        elif model_type == "rec":
            post_result = post_process_class(preds, batch_numpy[1])
            eval_class(post_result, batch_numpy)

        if rerun_flag:
            if batch_id == 3:
                print(
                    "***** Collect dynamic shape done, Please rerun the program to get correct results. *****"
                )
                return
        if batch_id % 100 == 0:
            print("Eval iter:", batch_id)
            sys.stdout.flush()

    metric = eval_class.get_metric()

    time_avg = predict_time / sample_nums
    print(
        "[Benchmark] Inference time(ms): min={}, max={}, avg={}".format(
            round(time_min * 1000, 2),
            round(time_max * 1000, 1),
            round(time_avg * 1000, 1),
        )
    )
    for k, v in metric.items():
        print("{}:{}".format(k, v))
    sys.stdout.flush()