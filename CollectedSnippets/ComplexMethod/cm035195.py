def __init__(self, args, logger=None):
        if os.path.exists(f"{args.det_model_dir}/inference.yml"):
            model_config = utility.load_config(f"{args.det_model_dir}/inference.yml")
            model_name = model_config.get("Global", {}).get("model_name", "")
            if model_name and model_name not in [
                "PP-OCRv5_mobile_det",
                "PP-OCRv5_server_det",
            ]:
                raise ValueError(
                    f"{model_name} is not supported. Please check if the model is supported by the PaddleOCR wheel."
                )

        if logger is None:
            logger = get_logger()
        self.args = args
        self.det_algorithm = args.det_algorithm
        self.use_onnx = args.use_onnx
        pre_process_list = [
            {
                "DetResizeForTest": {
                    "limit_side_len": args.det_limit_side_len,
                    "limit_type": args.det_limit_type,
                }
            },
            {
                "NormalizeImage": {
                    "std": [0.229, 0.224, 0.225],
                    "mean": [0.485, 0.456, 0.406],
                    "scale": "1./255.",
                    "order": "hwc",
                }
            },
            {"ToCHWImage": None},
            {"KeepKeys": {"keep_keys": ["image", "shape"]}},
        ]
        postprocess_params = {}
        if self.det_algorithm == "DB":
            postprocess_params["name"] = "DBPostProcess"
            postprocess_params["thresh"] = args.det_db_thresh
            postprocess_params["box_thresh"] = args.det_db_box_thresh
            postprocess_params["max_candidates"] = 1000
            postprocess_params["unclip_ratio"] = args.det_db_unclip_ratio
            postprocess_params["use_dilation"] = args.use_dilation
            postprocess_params["score_mode"] = args.det_db_score_mode
            postprocess_params["box_type"] = args.det_box_type
        elif self.det_algorithm == "DB++":
            postprocess_params["name"] = "DBPostProcess"
            postprocess_params["thresh"] = args.det_db_thresh
            postprocess_params["box_thresh"] = args.det_db_box_thresh
            postprocess_params["max_candidates"] = 1000
            postprocess_params["unclip_ratio"] = args.det_db_unclip_ratio
            postprocess_params["use_dilation"] = args.use_dilation
            postprocess_params["score_mode"] = args.det_db_score_mode
            postprocess_params["box_type"] = args.det_box_type
            pre_process_list[1] = {
                "NormalizeImage": {
                    "std": [1.0, 1.0, 1.0],
                    "mean": [0.48109378172549, 0.45752457890196, 0.40787054090196],
                    "scale": "1./255.",
                    "order": "hwc",
                }
            }
        elif self.det_algorithm == "EAST":
            postprocess_params["name"] = "EASTPostProcess"
            postprocess_params["score_thresh"] = args.det_east_score_thresh
            postprocess_params["cover_thresh"] = args.det_east_cover_thresh
            postprocess_params["nms_thresh"] = args.det_east_nms_thresh
        elif self.det_algorithm == "SAST":
            pre_process_list[0] = {
                "DetResizeForTest": {"resize_long": args.det_limit_side_len}
            }
            postprocess_params["name"] = "SASTPostProcess"
            postprocess_params["score_thresh"] = args.det_sast_score_thresh
            postprocess_params["nms_thresh"] = args.det_sast_nms_thresh

            if args.det_box_type == "poly":
                postprocess_params["sample_pts_num"] = 6
                postprocess_params["expand_scale"] = 1.2
                postprocess_params["shrink_ratio_of_width"] = 0.2
            else:
                postprocess_params["sample_pts_num"] = 2
                postprocess_params["expand_scale"] = 1.0
                postprocess_params["shrink_ratio_of_width"] = 0.3

        elif self.det_algorithm == "PSE":
            postprocess_params["name"] = "PSEPostProcess"
            postprocess_params["thresh"] = args.det_pse_thresh
            postprocess_params["box_thresh"] = args.det_pse_box_thresh
            postprocess_params["min_area"] = args.det_pse_min_area
            postprocess_params["box_type"] = args.det_box_type
            postprocess_params["scale"] = args.det_pse_scale
        elif self.det_algorithm == "FCE":
            pre_process_list[0] = {"DetResizeForTest": {"rescale_img": [1080, 736]}}
            postprocess_params["name"] = "FCEPostProcess"
            postprocess_params["scales"] = args.scales
            postprocess_params["alpha"] = args.alpha
            postprocess_params["beta"] = args.beta
            postprocess_params["fourier_degree"] = args.fourier_degree
            postprocess_params["box_type"] = args.det_box_type
        elif self.det_algorithm == "CT":
            pre_process_list[0] = {"ScaleAlignedShort": {"short_size": 640}}
            postprocess_params["name"] = "CTPostProcess"
        else:
            logger.info("unknown det_algorithm:{}".format(self.det_algorithm))
            sys.exit(0)

        self.preprocess_op = create_operators(pre_process_list)
        self.postprocess_op = build_post_process(postprocess_params)
        (
            self.predictor,
            self.input_tensor,
            self.output_tensors,
            self.config,
        ) = utility.create_predictor(args, "det", logger)

        if self.use_onnx:
            img_h, img_w = self.input_tensor.shape[2:]
            if isinstance(img_h, str) or isinstance(img_w, str):
                pass
            elif img_h is not None and img_w is not None and img_h > 0 and img_w > 0:
                pre_process_list[0] = {
                    "DetResizeForTest": {"image_shape": [img_h, img_w]}
                }
        self.preprocess_op = create_operators(pre_process_list)

        if args.benchmark:
            import auto_log

            pid = os.getpid()
            gpu_id = utility.get_infer_gpuid()
            self.autolog = auto_log.AutoLogger(
                model_name="det",
                model_precision=args.precision,
                batch_size=1,
                data_shape="dynamic",
                save_path=None,  # not used if logger is not None
                inference_config=self.config,
                pids=pid,
                process_name=None,
                gpu_ids=gpu_id if args.use_gpu else None,
                time_keys=["preprocess_time", "inference_time", "postprocess_time"],
                warmup=2,
                logger=logger,
            )