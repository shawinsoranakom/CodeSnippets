def __init__(self, configs: Union[dict, str] = None):
        # 设置默认配置文件路径
        configs_base_path: str = "GPT_SoVITS/configs/"
        os.makedirs(configs_base_path, exist_ok=True)
        self.configs_path: str = os.path.join(configs_base_path, "tts_infer.yaml")

        if configs in ["", None]:
            if not os.path.exists(self.configs_path):
                self.save_configs()
                print(f"Create default config file at {self.configs_path}")
            configs: dict = deepcopy(self.default_configs)

        if isinstance(configs, str):
            self.configs_path = configs
            configs: dict = self._load_configs(self.configs_path)

        assert isinstance(configs, dict)
        configs_ = deepcopy(self.default_configs)
        configs_.update(configs)
        self.configs: dict = configs_.get("custom", configs_["v2"])
        self.default_configs = deepcopy(configs_)

        self.device = self.configs.get("device", torch.device("cpu"))
        if "cuda" in str(self.device) and not torch.cuda.is_available():
            print("Warning: CUDA is not available, set device to CPU.")
            self.device = torch.device("cpu")

        self.is_half = self.configs.get("is_half", False)
        if str(self.device) == "cpu" and self.is_half:
            print(f"Warning: Half precision is not supported on CPU, set is_half to False.")
            self.is_half = False

        version = self.configs.get("version", None)
        self.version = version
        assert self.version in ["v1", "v2", "v3", "v4", "v2Pro", "v2ProPlus"], "Invalid version!"
        self.t2s_weights_path = self.configs.get("t2s_weights_path", None)
        self.vits_weights_path = self.configs.get("vits_weights_path", None)
        self.bert_base_path = self.configs.get("bert_base_path", None)
        self.cnhuhbert_base_path = self.configs.get("cnhuhbert_base_path", None)
        self.languages = self.v1_languages if self.version == "v1" else self.v2_languages

        self.use_vocoder: bool = False

        if (self.t2s_weights_path in [None, ""]) or (not os.path.exists(self.t2s_weights_path)):
            self.t2s_weights_path = self.default_configs[version]["t2s_weights_path"]
            print(f"fall back to default t2s_weights_path: {self.t2s_weights_path}")
        if (self.vits_weights_path in [None, ""]) or (not os.path.exists(self.vits_weights_path)):
            self.vits_weights_path = self.default_configs[version]["vits_weights_path"]
            print(f"fall back to default vits_weights_path: {self.vits_weights_path}")
        if (self.bert_base_path in [None, ""]) or (not os.path.exists(self.bert_base_path)):
            self.bert_base_path = self.default_configs[version]["bert_base_path"]
            print(f"fall back to default bert_base_path: {self.bert_base_path}")
        if (self.cnhuhbert_base_path in [None, ""]) or (not os.path.exists(self.cnhuhbert_base_path)):
            self.cnhuhbert_base_path = self.default_configs[version]["cnhuhbert_base_path"]
            print(f"fall back to default cnhuhbert_base_path: {self.cnhuhbert_base_path}")
        self.update_configs()

        self.max_sec = None
        self.hz: int = 50
        self.semantic_frame_rate: str = "25hz"
        self.segment_size: int = 20480
        self.filter_length: int = 2048
        self.sampling_rate: int = 32000
        self.hop_length: int = 640
        self.win_length: int = 2048
        self.n_speakers: int = 300