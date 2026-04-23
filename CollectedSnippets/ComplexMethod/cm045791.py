def __init__(self, *args, **kwargs):
        parser = utility.init_args()
        args = parser.parse_args(args)

        self.lang = kwargs.get('lang', 'ch')
        self.is_seal = self.lang in ['seal', 'seal_lite']
        self.enable_merge_det_boxes = kwargs.get("enable_merge_det_boxes", True)

        device = get_device()
        if device == 'cpu':
            if self.lang in ['ch', 'ch_server', 'japan', 'chinese_cht']:
                # logger.warning("The current device in use is CPU. To ensure the speed of parsing, the language is automatically switched to ch_lite.")
                self.lang = 'ch_lite'
            elif self.lang in ['seal']:
                self.lang = 'seal_lite'

        if self.lang in latin_lang:
            self.lang = 'latin'
        elif self.lang in east_slavic_lang:
            self.lang = 'east_slavic'
        elif self.lang in arabic_lang:
            self.lang = 'arabic'
        elif self.lang in cyrillic_lang:
            self.lang = 'cyrillic'
        elif self.lang in devanagari_lang:
            self.lang = 'devanagari'
        else:
            pass

        models_config_path = os.path.join(root_dir, 'pytorchocr', 'utils', 'resources', 'models_config.yml')
        with open(models_config_path) as file:
            config = yaml.safe_load(file)
            det, rec, dict_file = get_model_params(self.lang, config)
        ocr_models_dir = ModelPath.pytorch_paddle

        det_model_path = f"{ocr_models_dir}/{det}"
        det_model_path = os.path.join(auto_download_and_get_model_root_path(det_model_path), det_model_path)
        rec_model_path = f"{ocr_models_dir}/{rec}"
        rec_model_path = os.path.join(auto_download_and_get_model_root_path(rec_model_path), rec_model_path)
        kwargs['det_model_path'] = det_model_path
        kwargs['rec_model_path'] = rec_model_path
        kwargs['rec_char_dict_path'] = os.path.join(root_dir, 'pytorchocr', 'utils', 'resources', 'dict', dict_file)
        kwargs['rec_batch_num'] = 6
        if self.is_seal:
            kwargs['det_limit_side_len'] = 736
            kwargs['det_limit_type'] = 'min'
            kwargs['det_max_side_limit'] = 4000
            kwargs['det_db_thresh'] = 0.2
            kwargs['det_db_box_thresh'] = 0.6
            kwargs['det_db_unclip_ratio'] = 0.5
            kwargs['det_box_type'] = 'poly'
            kwargs['use_dilation'] = False
            kwargs['enable_merge_det_boxes'] = False
            kwargs['drop_score'] = 0
            self.enable_merge_det_boxes = False

        kwargs['device'] = device

        default_args = vars(args)
        default_args.update(kwargs)
        args = argparse.Namespace(**default_args)

        super().__init__(args)
        if self.is_seal:
            self._seal_sort_boxes = SortPolyBoxes()
            self._seal_crop_by_polys = CropByPolys(det_box_type='poly')
            self._seal_debug_counter = 0
            self._seal_debug_dir = self._resolve_seal_debug_dir()