def __init__(self, *args, vocoder=None, sampling_rate=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.vocoder = None
        if self.model.__class__ in MODEL_FOR_TEXT_TO_SPECTROGRAM_MAPPING.values():
            self.vocoder = (
                SpeechT5HifiGan.from_pretrained(DEFAULT_VOCODER_ID).to(self.model.device)
                if vocoder is None
                else vocoder
            )

        if self.model.config.model_type in ["musicgen", "speecht5"]:
            # MusicGen and SpeechT5 expect to use their tokenizer instead
            self.processor = None

        self.sampling_rate = sampling_rate
        if self.vocoder is not None:
            self.sampling_rate = self.vocoder.config.sampling_rate

        if self.sampling_rate is None:
            # get sampling_rate from config and generation config

            config = self.model.config
            gen_config = self.model.__dict__.get("generation_config", None)
            if gen_config is not None:
                config.update({k: v for k, v in gen_config.to_dict().items() if v is not None})

            for sampling_rate_name in ["sample_rate", "sampling_rate"]:
                sampling_rate = getattr(config, sampling_rate_name, None)
                if sampling_rate is not None:
                    self.sampling_rate = sampling_rate
                elif getattr(config, "codec_config", None) is not None:
                    sampling_rate = getattr(config.codec_config, sampling_rate_name, None)
                    if sampling_rate is not None:
                        self.sampling_rate = sampling_rate

        # last fallback to get the sampling rate based on processor
        if self.sampling_rate is None and self.processor is not None and hasattr(self.processor, "feature_extractor"):
            self.sampling_rate = self.processor.feature_extractor.sampling_rate