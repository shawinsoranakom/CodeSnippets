def __init__(
        self,
        config: MusicgenMelodyConfig = None,
        text_encoder: PreTrainedModel | None = None,
        audio_encoder: PreTrainedModel | None = None,
        decoder: MusicgenMelodyForCausalLM | None = None,
    ):
        r"""
        text_encoder (`PreTrainedModel`, *optional*):
            The text encoder model that encodes text into hidden states for conditioning.
        audio_encoder (`PreTrainedModel`, *optional*):
            The audio encoder model that encodes audio into hidden states for conditioning.
        decoder (`MusicgenMelodyForCausalLM`, *optional*):
            The decoder model that generates audio tokens based on conditioning signals.
        """
        if config is None and None in (text_encoder, audio_encoder, decoder):
            raise ValueError(
                "Either a configuration has to be provided, or all three of text encoder, audio encoder and Musicgen Melody decoder."
            )
        if config is None:
            config = MusicgenMelodyConfig(
                text_encoder=text_encoder.config, audio_encoder=audio_encoder.config, decoder=decoder.config
            )
        else:
            if not isinstance(config, self.config_class):
                raise ValueError(f"Config: {config} has to be of type {self.config_class}")

        # initialize with config
        super().__init__(config)

        if text_encoder is None:
            text_encoder = AutoModelForTextEncoding.from_config(config.text_encoder)

        if audio_encoder is None:
            audio_encoder = AutoModel.from_config(config.audio_encoder)

        if decoder is None:
            decoder = MusicgenMelodyForCausalLM._from_config(config.decoder)

        self.text_encoder = text_encoder
        self.audio_encoder = audio_encoder
        self.decoder = decoder

        # make sure that the individual model's config refers to the shared config
        # so that the updates to the config will be synced
        self.config.text_encoder._attn_implementation = self.text_encoder.config._attn_implementation
        self.config.audio_encoder._attn_implementation = self.audio_encoder.config._attn_implementation
        self.config.decoder._attn_implementation = self.decoder.config._attn_implementation
        self.text_encoder.config = self.config.text_encoder
        self.audio_encoder.config = self.config.audio_encoder
        self.decoder.config = self.config.decoder

        # text encoder outputs might need to be projected to different dimension for decoder
        if self.text_encoder.config.hidden_size != self.decoder.config.hidden_size:
            self.enc_to_dec_proj = nn.Linear(self.text_encoder.config.hidden_size, self.decoder.config.hidden_size)

        # audio encoder outputs after chroma extraction might need to be projected to different dimension for decoder
        if self.config.num_chroma != self.decoder.config.hidden_size:
            self.audio_enc_to_dec_proj = nn.Linear(self.config.num_chroma, self.decoder.config.hidden_size)

        if self.text_encoder.get_output_embeddings() is not None:
            raise ValueError(
                f"The encoder {self.text_encoder} should not have a LM Head. Please use a model without and LM Head"
            )

        # Initialize projection layers weights and tie text encoder and decoder weights if set accordingly
        self.post_init()