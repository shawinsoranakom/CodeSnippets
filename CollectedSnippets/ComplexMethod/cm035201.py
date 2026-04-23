def __init__(self, args, logger=None):
        if os.path.exists(f"{args.rec_model_dir}/inference.yml"):
            model_config = utility.load_config(f"{args.rec_model_dir}/inference.yml")
            model_name = model_config.get("Global", {}).get("model_name", "")
            if model_name and model_name not in [
                "PP-OCRv5_mobile_rec",
                "PP-OCRv5_server_rec",
                "korean_PP-OCRv5_mobile_rec",
                "eslav_PP-OCRv5_mobile_rec",
                "latin_PP-OCRv5_mobile_rec",
                "en_PP-OCRv5_mobile_rec",
                "th_PP-OCRv5_mobile_rec",
                "el_PP-OCRv5_mobile_rec",
            ]:
                raise ValueError(
                    f"{model_name} is not supported. Please check if the model is supported by the PaddleOCR wheel."
                )

            if args.rec_char_dict_path == "./ppocr/utils/ppocr_keys_v1.txt":
                rec_char_list = model_config.get("PostProcess", {}).get(
                    "character_dict", []
                )
                if rec_char_list:
                    new_rec_char_dict_path = f"{args.rec_model_dir}/ppocr_keys.txt"
                    with open(new_rec_char_dict_path, "w", encoding="utf-8") as f:
                        f.writelines([char + "\n" for char in rec_char_list])
                    args.rec_char_dict_path = new_rec_char_dict_path

        if logger is None:
            logger = get_logger()
        self.rec_image_shape = [int(v) for v in args.rec_image_shape.split(",")]
        self.rec_batch_num = args.rec_batch_num
        self.rec_algorithm = args.rec_algorithm
        postprocess_params = {
            "name": "CTCLabelDecode",
            "character_dict_path": args.rec_char_dict_path,
            "use_space_char": args.use_space_char,
        }
        if self.rec_algorithm == "SRN":
            postprocess_params = {
                "name": "SRNLabelDecode",
                "character_dict_path": args.rec_char_dict_path,
                "use_space_char": args.use_space_char,
            }
        elif self.rec_algorithm == "RARE":
            postprocess_params = {
                "name": "AttnLabelDecode",
                "character_dict_path": args.rec_char_dict_path,
                "use_space_char": args.use_space_char,
            }
        elif self.rec_algorithm == "NRTR":
            postprocess_params = {
                "name": "NRTRLabelDecode",
                "character_dict_path": args.rec_char_dict_path,
                "use_space_char": args.use_space_char,
            }
        elif self.rec_algorithm == "SAR":
            postprocess_params = {
                "name": "SARLabelDecode",
                "character_dict_path": args.rec_char_dict_path,
                "use_space_char": args.use_space_char,
            }
        elif self.rec_algorithm == "VisionLAN":
            postprocess_params = {
                "name": "VLLabelDecode",
                "character_dict_path": args.rec_char_dict_path,
                "use_space_char": args.use_space_char,
                "max_text_length": args.max_text_length,
            }
        elif self.rec_algorithm == "ViTSTR":
            postprocess_params = {
                "name": "ViTSTRLabelDecode",
                "character_dict_path": args.rec_char_dict_path,
                "use_space_char": args.use_space_char,
            }
        elif self.rec_algorithm == "ABINet":
            postprocess_params = {
                "name": "ABINetLabelDecode",
                "character_dict_path": args.rec_char_dict_path,
                "use_space_char": args.use_space_char,
            }
        elif self.rec_algorithm == "SPIN":
            postprocess_params = {
                "name": "SPINLabelDecode",
                "character_dict_path": args.rec_char_dict_path,
                "use_space_char": args.use_space_char,
            }
        elif self.rec_algorithm == "RobustScanner":
            postprocess_params = {
                "name": "SARLabelDecode",
                "character_dict_path": args.rec_char_dict_path,
                "use_space_char": args.use_space_char,
                "rm_symbol": True,
            }
        elif self.rec_algorithm == "RFL":
            postprocess_params = {
                "name": "RFLLabelDecode",
                "character_dict_path": None,
                "use_space_char": args.use_space_char,
            }
        elif self.rec_algorithm == "SATRN":
            postprocess_params = {
                "name": "SATRNLabelDecode",
                "character_dict_path": args.rec_char_dict_path,
                "use_space_char": args.use_space_char,
                "rm_symbol": True,
            }
        elif self.rec_algorithm in ["CPPD", "CPPDPadding"]:
            postprocess_params = {
                "name": "CPPDLabelDecode",
                "character_dict_path": args.rec_char_dict_path,
                "use_space_char": args.use_space_char,
                "rm_symbol": True,
            }
        elif self.rec_algorithm == "PREN":
            postprocess_params = {"name": "PRENLabelDecode"}
        elif self.rec_algorithm == "CAN":
            self.inverse = args.rec_image_inverse
            postprocess_params = {
                "name": "CANLabelDecode",
                "character_dict_path": args.rec_char_dict_path,
                "use_space_char": args.use_space_char,
            }
        elif self.rec_algorithm == "LaTeXOCR":
            postprocess_params = {
                "name": "LaTeXOCRDecode",
                "rec_char_dict_path": args.rec_char_dict_path,
            }
        elif self.rec_algorithm == "ParseQ":
            postprocess_params = {
                "name": "ParseQLabelDecode",
                "character_dict_path": args.rec_char_dict_path,
                "use_space_char": args.use_space_char,
            }
        self.postprocess_op = build_post_process(postprocess_params)
        self.postprocess_params = postprocess_params
        (
            self.predictor,
            self.input_tensor,
            self.output_tensors,
            self.config,
        ) = utility.create_predictor(args, "rec", logger)
        self.benchmark = args.benchmark
        self.use_onnx = args.use_onnx
        if args.benchmark:
            import auto_log

            pid = os.getpid()
            gpu_id = utility.get_infer_gpuid()
            self.autolog = auto_log.AutoLogger(
                model_name="rec",
                model_precision=args.precision,
                batch_size=args.rec_batch_num,
                data_shape="dynamic",
                save_path=None,  # not used if logger is not None
                inference_config=self.config,
                pids=pid,
                process_name=None,
                gpu_ids=gpu_id if args.use_gpu else None,
                time_keys=["preprocess_time", "inference_time", "postprocess_time"],
                warmup=0,
                logger=logger,
            )
        self.return_word_box = args.return_word_box