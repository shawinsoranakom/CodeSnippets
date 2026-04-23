def load_predictor(args):
    """
    load predictor func
    """
    rerun_flag = False
    model_file = os.path.join(args.model_path, args.model_filename)
    params_file = os.path.join(args.model_path, args.params_filename)
    pred_cfg = PredictConfig(model_file, params_file)
    pred_cfg.enable_memory_optim()
    pred_cfg.switch_ir_optim(True)
    if args.device == "GPU":
        pred_cfg.enable_use_gpu(100, 0)
    else:
        pred_cfg.disable_gpu()
        pred_cfg.set_cpu_math_library_num_threads(args.cpu_threads)
        if args.use_mkldnn:
            pred_cfg.enable_mkldnn()
            if args.precision == "int8":
                pred_cfg.enable_mkldnn_int8({"conv2d"})

            if global_config["model_type"] == "rec":
                # delete pass which influence the accuracy, please refer to https://github.com/PaddlePaddle/Paddle/issues/55290
                pred_cfg.delete_pass("fc_mkldnn_pass")
                pred_cfg.delete_pass("fc_act_mkldnn_fuse_pass")

    if args.use_trt:
        # To collect the dynamic shapes of inputs for TensorRT engine
        dynamic_shape_file = os.path.join(args.model_path, "dynamic_shape.txt")
        if os.path.exists(dynamic_shape_file):
            pred_cfg.enable_tuned_tensorrt_dynamic_shape(dynamic_shape_file, True)
            print("trt set dynamic shape done!")
            precision_map = {
                "fp16": PrecisionType.Half,
                "fp32": PrecisionType.Float32,
                "int8": PrecisionType.Int8,
            }
            if (
                args.precision == "int8"
                and "ppocrv4_det_server_qat_dist.yaml" in args.config_path
            ):
                # Use the following settings only when the hardware is a Tesla V100. If you are using
                # a RTX 3090, use the settings in the else branch.
                pred_cfg.enable_tensorrt_engine(
                    workspace_size=1 << 30,
                    max_batch_size=1,
                    min_subgraph_size=30,
                    precision_mode=precision_map[args.precision],
                    use_static=True,
                    use_calib_mode=False,
                )
                pred_cfg.exp_disable_tensorrt_ops(["elementwise_add"])
            else:
                pred_cfg.enable_tensorrt_engine(
                    workspace_size=1 << 30,
                    max_batch_size=1,
                    min_subgraph_size=4,
                    precision_mode=precision_map[args.precision],
                    use_static=True,
                    use_calib_mode=False,
                )
        else:
            # pred_cfg.disable_gpu()
            # pred_cfg.set_cpu_math_library_num_threads(24)
            pred_cfg.collect_shape_range_info(dynamic_shape_file)
            print("Start collect dynamic shape...")
            rerun_flag = True

    predictor = create_predictor(pred_cfg)
    return predictor, rerun_flag