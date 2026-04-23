def __init__(
        self,
        config: MusicgenConfig | None = None,
        text_encoder: PreTrainedModel | None = None,
        audio_encoder: PreTrainedModel | None = None,
        decoder: MusicgenForCausalLM | None = None,
    ):
        r"""
        text_encoder (`PreTrainedModel`, *optional*):
            The text encoder model that encodes text into hidden states for conditioning.
        audio_encoder (`PreTrainedModel`, *optional*):
            The audio encoder model that encodes audio into hidden states for conditioning.
        decoder (`MusicgenForCausalLM`, *optional*):
            The decoder model that generates audio tokens based on conditioning signals.
        """
        if config is None and (text_encoder is None or audio_encoder is None or decoder is None):
            raise ValueError(
                "Either a configuration has to be provided, or all three of text encoder, audio encoder and MusicGen decoder."
            )
        if config is None:
            config = MusicgenConfig(
                text_encoder=text_encoder.config, audio_encoder=audio_encoder.config, decoder=decoder.config
            )
        else:
            if not isinstance(config, self.config_class):
                raise ValueError(f"Config: {config} has to be of type {self.config_class}")

        if config.decoder.cross_attention_hidden_size is not None:
            if config.decoder.cross_attention_hidden_size != config.text_encoder.hidden_size:
                raise ValueError(
                    "If `cross_attention_hidden_size` is specified in the MusicGen decoder's configuration, it has to be equal"
                    f" to the text encoder's `hidden_size`. Got {config.decoder.cross_attention_hidden_size} for"
                    f" `config.decoder.cross_attention_hidden_size` and {config.text_encoder.hidden_size} for"
                    " `config.text_encoder.hidden_size`."
                )

        # initialize with config
        super().__init__(config)

        if text_encoder is None:
            from ..auto.modeling_auto import AutoModelForTextEncoding

            text_encoder = AutoModelForTextEncoding.from_config(config.text_encoder)

        if audio_encoder is None:
            from ..auto.modeling_auto import AutoModel

            audio_encoder = AutoModel.from_config(config.audio_encoder)

        if decoder is None:
            decoder = MusicgenForCausalLM._from_config(config.decoder)

        self.text_encoder = text_encoder
        self.audio_encoder = audio_encoder
        self.decoder = decoder

        if self.text_encoder.config.to_dict() != self.config.text_encoder.to_dict():
            logger.warning(
                f"Config of the text_encoder: {self.text_encoder.__class__} is overwritten by shared text_encoder config:"
                f" {self.config.text_encoder}"
            )
        if self.audio_encoder.config.to_dict() != self.config.audio_encoder.to_dict():
            logger.warning(
                f"Config of the audio_encoder: {self.audio_encoder.__class__} is overwritten by shared audio_encoder config:"
                f" {self.config.audio_encoder}"
            )
        if self.decoder.config.to_dict() != self.config.decoder.to_dict():
            logger.warning(
                f"Config of the decoder: {self.decoder.__class__} is overwritten by shared decoder config:"
                f" {self.config.decoder}"
            )

        # make sure that the individual model's config refers to the shared config
        # so that the updates to the config will be synced
        self.config.text_encoder._attn_implementation = self.text_encoder.config._attn_implementation
        self.config.audio_encoder._attn_implementation = self.audio_encoder.config._attn_implementation
        self.config.decoder._attn_implementation = self.decoder.config._attn_implementation
        self.text_encoder.config = self.config.text_encoder
        self.audio_encoder.config = self.config.audio_encoder
        self.decoder.config = self.config.decoder

        # text encoder outputs might need to be projected to different dimension for decoder
        if (
            self.text_encoder.config.hidden_size != self.decoder.config.hidden_size
            and self.decoder.config.cross_attention_hidden_size is None
        ):
            self.enc_to_dec_proj = nn.Linear(self.text_encoder.config.hidden_size, self.decoder.config.hidden_size)

        if self.text_encoder.get_output_embeddings() is not None:
            raise ValueError(
                f"The encoder {self.text_encoder} should not have a LM Head. Please use a model without and LM Head"
            )

        decoder_signature = set(inspect.signature(self.decoder.forward).parameters.keys())
        if "encoder_hidden_states" not in decoder_signature:
            raise ValueError(
                "The selected decoder is not prepared for the encoder hidden states to be passed. Please see the "
                "following discussion on GitHub: https://github.com/huggingface/transformers/issues/23350"
            )

        # tie text encoder, decoder weights if config set accordingly
        self.post_init()