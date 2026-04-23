def init_vits_weights(self, weights_path: str):
        self.configs.vits_weights_path = weights_path
        version, model_version, if_lora_v3 = get_sovits_version_from_path_fast(weights_path)
        if "Pro" in model_version:
            self.init_sv_model()
        path_sovits = self.configs.default_configs[model_version]["vits_weights_path"]

        if if_lora_v3 == True and os.path.exists(path_sovits) == False:
            info = path_sovits + i18n("SoVITS %s 底模缺失，无法加载相应 LoRA 权重" % model_version)
            raise FileNotFoundError(info)

        # dict_s2 = torch.load(weights_path, map_location=self.configs.device,weights_only=False)
        dict_s2 = load_sovits_new(weights_path)
        hps = dict_s2["config"]
        hps["model"]["semantic_frame_rate"] = "25hz"
        if "enc_p.text_embedding.weight" not in dict_s2["weight"]:
            hps["model"]["version"] = "v2"  # v3model,v2sybomls
        elif dict_s2["weight"]["enc_p.text_embedding.weight"].shape[0] == 322:
            hps["model"]["version"] = "v1"
        else:
            hps["model"]["version"] = "v2"
        version = hps["model"]["version"]
        v3v4set = {"v3", "v4"}
        if model_version not in v3v4set:
            if "Pro" not in model_version:
                model_version = version
            else:
                hps["model"]["version"] = model_version
        else:
            hps["model"]["version"] = model_version

        self.configs.filter_length = hps["data"]["filter_length"]
        self.configs.segment_size = hps["train"]["segment_size"]
        self.configs.sampling_rate = hps["data"]["sampling_rate"]
        self.configs.hop_length = hps["data"]["hop_length"]
        self.configs.win_length = hps["data"]["win_length"]
        self.configs.n_speakers = hps["data"]["n_speakers"]
        self.configs.semantic_frame_rate = hps["model"]["semantic_frame_rate"]
        kwargs = hps["model"]
        # print(f"self.configs.sampling_rate:{self.configs.sampling_rate}")

        self.configs.update_version(model_version)

        # print(f"model_version:{model_version}")
        # print(f'hps["model"]["version"]:{hps["model"]["version"]}')
        if model_version not in v3v4set:
            vits_model = SynthesizerTrn(
                self.configs.filter_length // 2 + 1,
                self.configs.segment_size // self.configs.hop_length,
                n_speakers=self.configs.n_speakers,
                **kwargs,
            )
            self.configs.use_vocoder = False
        else:
            kwargs["version"] = model_version
            vits_model = SynthesizerTrnV3(
                self.configs.filter_length // 2 + 1,
                self.configs.segment_size // self.configs.hop_length,
                n_speakers=self.configs.n_speakers,
                **kwargs,
            )
            self.configs.use_vocoder = True
            self.init_vocoder(model_version)
            if "pretrained" not in weights_path and hasattr(vits_model, "enc_q"):
                del vits_model.enc_q

        self.is_v2pro = model_version in {"v2Pro", "v2ProPlus"}

        if if_lora_v3 == False:
            print(
                f"Loading VITS weights from {weights_path}. {vits_model.load_state_dict(dict_s2['weight'], strict=False)}"
            )
        else:
            print(
                f"Loading VITS pretrained weights from {weights_path}. {vits_model.load_state_dict(load_sovits_new(path_sovits)['weight'], strict=False)}"
            )
            lora_rank = dict_s2["lora_rank"]
            lora_config = LoraConfig(
                target_modules=["to_k", "to_q", "to_v", "to_out.0"],
                r=lora_rank,
                lora_alpha=lora_rank,
                init_lora_weights=True,
            )
            vits_model.cfm = get_peft_model(vits_model.cfm, lora_config)
            print(
                f"Loading LoRA weights from {weights_path}. {vits_model.load_state_dict(dict_s2['weight'], strict=False)}"
            )

            vits_model.cfm = vits_model.cfm.merge_and_unload()

        vits_model = vits_model.to(self.configs.device)
        vits_model = vits_model.eval()

        self.vits_model = vits_model
        if self.configs.is_half and str(self.configs.device) != "cpu":
            self.vits_model = self.vits_model.half()

        self.configs.save_configs()