def create_predictor(args, mode, logger):
    if mode == "det":
        model_dir = args.det_model_dir
    elif mode == "cls":
        model_dir = args.cls_model_dir
    elif mode == "rec":
        model_dir = args.rec_model_dir
    elif mode == "table":
        model_dir = args.table_model_dir
    elif mode == "ser":
        model_dir = args.ser_model_dir
    elif mode == "re":
        model_dir = args.re_model_dir
    elif mode == "sr":
        model_dir = args.sr_model_dir
    elif mode == "layout":
        model_dir = args.layout_model_dir
    else:
        model_dir = args.e2e_model_dir

    if model_dir is None:
        logger.info("not find {} model file path {}".format(mode, model_dir))
        sys.exit(0)
    if args.use_onnx:
        import onnxruntime as ort

        model_file_path = model_dir
        if not os.path.exists(model_file_path):
            raise ValueError("not find model file path {}".format(model_file_path))

        sess_options = args.onnx_sess_options or None

        if args.onnx_providers and len(args.onnx_providers) > 0:
            sess = ort.InferenceSession(
                model_file_path,
                providers=args.onnx_providers,
                sess_options=sess_options,
            )
        elif args.use_gpu:
            sess = ort.InferenceSession(
                model_file_path,
                providers=[
                    (
                        "CUDAExecutionProvider",
                        {"device_id": args.gpu_id, "cudnn_conv_algo_search": "DEFAULT"},
                    )
                ],
                sess_options=sess_options,
            )
        else:
            sess = ort.InferenceSession(
                model_file_path,
                providers=["CPUExecutionProvider"],
                sess_options=sess_options,
            )
        inputs = sess.get_inputs()
        return (
            sess,
            inputs[0] if len(inputs) == 1 else [vo.name for vo in inputs],
            None,
            None,
        )

    else:
        file_names = ["model", "inference"]
        for file_name in file_names:
            params_file_path = f"{model_dir}/{file_name}.pdiparams"
            if os.path.exists(params_file_path):
                break

        if not os.path.exists(params_file_path):
            raise ValueError(f"not find {file_name}.pdiparams in {model_dir}")

        if not (
            os.path.exists(f"{model_dir}/{file_name}.pdmodel")
            or os.path.exists(f"{model_dir}/{file_name}.json")
        ):
            raise ValueError(
                f"neither {file_name}.json nor {file_name}.pdmodel was found in {model_dir}."
            )

        if os.path.exists(f"{model_dir}/{file_name}.json"):
            model_file_path = f"{model_dir}/{file_name}.json"
        else:
            model_file_path = f"{model_dir}/{file_name}.pdmodel"

        config = inference.Config(model_file_path, params_file_path)

        if hasattr(args, "precision"):
            if args.precision == "fp16" and args.use_tensorrt:
                precision = inference.PrecisionType.Half
            elif args.precision == "int8":
                precision = inference.PrecisionType.Int8
            else:
                precision = inference.PrecisionType.Float32
        else:
            precision = inference.PrecisionType.Float32

        if args.use_gpu:
            gpu_id = get_infer_gpuid()
            if gpu_id is None:
                logger.warning(
                    "GPU is not found in current device by nvidia-smi. Please check your device or ignore it if run on jetson."
                )
            config.enable_use_gpu(args.gpu_mem, args.gpu_id)
            if args.use_tensorrt:
                if ".json" in model_file_path:
                    trt_dynamic_shapes = {}
                    trt_dynamic_shape_input_data = {}
                    if os.path.exists(f"{model_dir}/inference.yml"):
                        model_config = load_config(f"{model_dir}/inference.yml")
                        trt_dynamic_shapes = (
                            model_config.get("Hpi", {})
                            .get("backend_configs", {})
                            .get("paddle_infer", {})
                            .get("trt_dynamic_shapes", {})
                        )
                        trt_dynamic_shape_input_data = (
                            model_config.get("Hpi", {})
                            .get("backend_configs", {})
                            .get("paddle_infer", {})
                            .get("trt_dynamic_shapes_input_data", {})
                        )

                    if not trt_dynamic_shapes:
                        raise RuntimeError(
                            "Configuration Error: 'trt_dynamic_shapes' must be defined in 'inference.yml' for Paddle Inference TensorRT."
                        )

                    trt_save_path = f"{model_dir}/.cache/trt/{file_name}"
                    trt_model_file_path = trt_save_path + ".json"
                    trt_params_file_path = trt_save_path + ".pdiparams"
                    if not os.path.exists(trt_model_file_path) or not os.path.exists(
                        trt_params_file_path
                    ):
                        _convert_trt(
                            {},
                            model_file_path,
                            params_file_path,
                            trt_save_path,
                            args.gpu_id,
                            trt_dynamic_shapes,
                            trt_dynamic_shape_input_data,
                        )
                    config = inference.Config(model_file_path, params_file_path)
                    config.exp_disable_mixed_precision_ops({"feed", "fetch"})
                    config.enable_use_gpu(args.gpu_mem, args.gpu_id)
                else:
                    config.enable_tensorrt_engine(
                        workspace_size=1 << 30,
                        precision_mode=precision,
                        max_batch_size=args.max_batch_size,
                        min_subgraph_size=args.min_subgraph_size,  # skip the minimum trt subgraph
                        use_calib_mode=False,
                    )

                    # collect shape
                    trt_shape_f = os.path.join(
                        model_dir, f"{mode}_trt_dynamic_shape.txt"
                    )

                    if not os.path.exists(trt_shape_f):
                        config.collect_shape_range_info(trt_shape_f)
                        logger.info(f"collect dynamic shape info into : {trt_shape_f}")
                    try:
                        config.enable_tuned_tensorrt_dynamic_shape(trt_shape_f, True)
                    except Exception as E:
                        logger.info(E)
                        logger.info("Please keep your paddlepaddle-gpu >= 2.3.0!")

        elif args.use_npu:
            config.enable_custom_device("npu")
        elif args.use_mlu:
            config.enable_custom_device("mlu")
        elif args.use_metax_gpu:
            if args.precision == "fp16":
                config.enable_custom_device(
                    "metax_gpu", 0, paddle.inference.PrecisionType.Half
                )

            else:
                config.enable_custom_device("metax_gpu")
        elif args.use_xpu:
            config.enable_xpu(10 * 1024 * 1024)
        elif args.use_gcu:  # for Enflame GCU(General Compute Unit)
            assert paddle.device.is_compiled_with_custom_device("gcu"), (
                "Args use_gcu cannot be set as True while your paddle "
                "is not compiled with gcu! \nPlease try: \n"
                "\t1. Install paddle-custom-gcu to run model on GCU. \n"
                "\t2. Set use_gcu as False in args to run model on CPU."
            )
            import paddle_custom_device.gcu.passes as gcu_passes

            gcu_passes.setUp()
            if args.precision == "fp16":
                config.enable_custom_device(
                    "gcu", 0, paddle.inference.PrecisionType.Half
                )
                gcu_passes.set_exp_enable_mixed_precision_ops(config)
            else:
                config.enable_custom_device("gcu")

            if paddle.framework.use_pir_api():
                config.enable_new_ir(True)
                config.enable_new_executor(True)
            else:
                pass_builder = config.pass_builder()
                gcu_passes.append_passes_for_legacy_ir(pass_builder, "PaddleOCR")
        else:
            config.disable_gpu()
            if args.enable_mkldnn is not None:
                if args.enable_mkldnn:
                    # cache 10 different shapes for mkldnn to avoid memory leak
                    config.set_mkldnn_cache_capacity(10)
                    config.enable_mkldnn()
                    if args.precision == "fp16":
                        config.enable_mkldnn_bfloat16()
                else:
                    if hasattr(config, "disable_mkldnn"):
                        config.disable_mkldnn()

            if hasattr(args, "cpu_threads"):
                config.set_cpu_math_library_num_threads(args.cpu_threads)
            else:
                # default cpu threads as 10
                config.set_cpu_math_library_num_threads(10)

            if hasattr(config, "enable_new_ir"):
                config.enable_new_ir()
            if hasattr(config, "enable_new_executor"):
                config.enable_new_executor()

        # enable memory optim
        config.enable_memory_optim()
        config.disable_glog_info()
        if not args.use_gcu:  # for Enflame GCU(General Compute Unit)
            config.delete_pass("conv_transpose_eltwiseadd_bn_fuse_pass")
        config.delete_pass("matmul_transpose_reshape_fuse_pass")
        if mode == "rec" and args.rec_algorithm == "SRN":
            config.delete_pass("gpu_cpu_map_matmul_v2_to_matmul_pass")
        if mode == "re":
            config.delete_pass("simplify_with_basic_ops_pass")
        if mode == "table":
            config.delete_pass("fc_fuse_pass")  # not supported for table
        config.switch_use_feed_fetch_ops(False)
        config.switch_ir_optim(True)

        # create predictor
        predictor = inference.create_predictor(config)
        input_names = predictor.get_input_names()
        if mode in ["ser", "re"]:
            input_tensor = []
            for name in input_names:
                input_tensor.append(predictor.get_input_handle(name))
        else:
            for name in input_names:
                input_tensor = predictor.get_input_handle(name)
        output_tensors = get_output_tensors(args, mode, predictor)
        return predictor, input_tensor, output_tensors, config