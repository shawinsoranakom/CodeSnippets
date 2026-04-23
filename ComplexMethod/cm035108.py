def __init__(self, args):
        self.mode = args.mode
        self.recovery = args.recovery

        self.image_orientation_predictor = None
        if args.image_orientation:
            import paddleclas

            self.image_orientation_predictor = paddleclas.PaddleClas(
                model_name="text_image_orientation"
            )

        if self.mode == "structure":
            if not args.show_log:
                logger.setLevel(logging.INFO)
            if args.layout == False and args.ocr == True:
                args.ocr = False
                logger.warning(
                    "When args.layout is false, args.ocr is automatically set to false"
                )
            # init model
            self.layout_predictor = None
            self.text_system = None
            self.table_system = None
            self.formula_system = None
            if args.layout:
                self.layout_predictor = LayoutPredictor(args)
                if args.ocr:
                    self.text_system = TextSystem(args)
            if args.table:
                if self.text_system is not None:
                    self.table_system = TableSystem(
                        args,
                        self.text_system.text_detector,
                        self.text_system.text_recognizer,
                    )
                else:
                    self.table_system = TableSystem(args)
            if args.formula:
                args_formula = deepcopy(args)
                args_formula.rec_algorithm = args.formula_algorithm
                args_formula.rec_model_dir = args.formula_model_dir
                args_formula.rec_char_dict_path = args.formula_char_dict_path
                args_formula.rec_batch_num = args.formula_batch_num
                self.formula_system = TextRecognizer(args_formula)

        elif self.mode == "kie":
            from ppstructure.kie.predict_kie_token_ser_re import SerRePredictor

            self.kie_predictor = SerRePredictor(args)

        self.return_word_box = args.return_word_box