def __init_qianfan(self):
        self.model = self.config.model
        if self.config.access_key and self.config.secret_key:
            # for system level auth, use access_key and secret_key, recommended by official
            # set environment variable due to official recommendation
            os.environ.setdefault("QIANFAN_ACCESS_KEY", self.config.access_key)
            os.environ.setdefault("QIANFAN_SECRET_KEY", self.config.secret_key)
        elif self.config.api_key and self.config.secret_key:
            # for application level auth, use api_key and secret_key
            # set environment variable due to official recommendation
            os.environ.setdefault("QIANFAN_AK", self.config.api_key)
            os.environ.setdefault("QIANFAN_SK", self.config.secret_key)
        else:
            raise ValueError("Set the `access_key`&`secret_key` or `api_key`&`secret_key` first")

        if self.config.base_url:
            os.environ.setdefault("QIANFAN_BASE_URL", self.config.base_url)

        support_system_pairs = [
            ("ERNIE-Bot-4", "completions_pro"),  # (model, corresponding-endpoint)
            ("ERNIE-Bot-8k", "ernie_bot_8k"),
            ("ERNIE-Bot", "completions"),
            ("ERNIE-Bot-turbo", "eb-instant"),
            ("ERNIE-Speed", "ernie_speed"),
            ("EB-turbo-AppBuilder", "ai_apaas"),
        ]
        if self.model in [pair[0] for pair in support_system_pairs]:
            # only some ERNIE models support
            self.use_system_prompt = True
        if self.config.endpoint in [pair[1] for pair in support_system_pairs]:
            self.use_system_prompt = True

        assert not (self.model and self.config.endpoint), "Only set `model` or `endpoint` in the config"
        assert self.model or self.config.endpoint, "Should set one of `model` or `endpoint` in the config"

        self.token_costs = copy.deepcopy(QIANFAN_MODEL_TOKEN_COSTS)
        self.token_costs.update(QIANFAN_ENDPOINT_TOKEN_COSTS)

        # self deployed model on the cloud not to calculate usage, it charges resource pool rental fee
        self.calc_usage = self.config.calc_usage and self.config.endpoint is None
        self.aclient: ChatCompletion = qianfan.ChatCompletion()