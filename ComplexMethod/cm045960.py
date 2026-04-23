def __init__(self, args, **kwargs):
        self.device = args.device
        self.rec_image_shape = [int(v) for v in args.rec_image_shape.split(",")]
        self.character_type = args.rec_char_type
        self.rec_batch_num = args.rec_batch_num
        self.rec_algorithm = args.rec_algorithm
        self.max_text_length = args.max_text_length
        postprocess_params = {
            'name': 'CTCLabelDecode',
            "character_type": args.rec_char_type,
            "character_dict_path": args.rec_char_dict_path,
            "use_space_char": args.use_space_char
        }
        if self.rec_algorithm == "SRN":
            postprocess_params = {
                'name': 'SRNLabelDecode',
                "character_type": args.rec_char_type,
                "character_dict_path": args.rec_char_dict_path,
                "use_space_char": args.use_space_char
            }
        elif self.rec_algorithm == "RARE":
            postprocess_params = {
                'name': 'AttnLabelDecode',
                "character_type": args.rec_char_type,
                "character_dict_path": args.rec_char_dict_path,
                "use_space_char": args.use_space_char
            }
        elif self.rec_algorithm == 'NRTR':
            postprocess_params = {
                'name': 'NRTRLabelDecode',
                "character_dict_path": args.rec_char_dict_path,
                "use_space_char": args.use_space_char
            }
        elif self.rec_algorithm == "SAR":
            postprocess_params = {
                'name': 'SARLabelDecode',
                "character_dict_path": args.rec_char_dict_path,
                "use_space_char": args.use_space_char
            }
        elif self.rec_algorithm == 'ViTSTR':
            postprocess_params = {
                'name': 'ViTSTRLabelDecode',
                "character_dict_path": args.rec_char_dict_path,
                "use_space_char": args.use_space_char
            }
        elif self.rec_algorithm == "CAN":
            self.inverse = args.rec_image_inverse
            postprocess_params = {
                'name': 'CANLabelDecode',
                "character_dict_path": args.rec_char_dict_path,
                "use_space_char": args.use_space_char
            }
        elif self.rec_algorithm == 'RFL':
            postprocess_params = {
                'name': 'RFLLabelDecode',
                "character_dict_path": None,
                "use_space_char": args.use_space_char
            }
        self.postprocess_op = build_post_process(postprocess_params)

        self.limited_max_width = args.limited_max_width
        self.limited_min_width = args.limited_min_width

        self.weights_path = args.rec_model_path
        self.yaml_path = args.rec_yaml_path

        network_config = utility.get_arch_config(self.weights_path)
        weights = self.read_pytorch_weights(self.weights_path)

        self.out_channels = self.get_out_channels(weights)
        if self.rec_algorithm == 'NRTR':
            self.out_channels = list(weights.values())[-1].numpy().shape[0]
        elif self.rec_algorithm == 'SAR':
            self.out_channels = list(weights.values())[-3].numpy().shape[0]

        kwargs['out_channels'] = self.out_channels
        super(TextRecognizer, self).__init__(network_config, **kwargs)

        self.load_state_dict(weights)
        self.net.eval()
        self.net.to(self.device)
        for module in self.net.modules():
            if isinstance(module, ConvBNAct):
                if module.use_act:
                    torch.quantization.fuse_modules(module, ['conv', 'bn', 'act'], inplace=True)
                else:
                    torch.quantization.fuse_modules(module, ['conv', 'bn'], inplace=True)