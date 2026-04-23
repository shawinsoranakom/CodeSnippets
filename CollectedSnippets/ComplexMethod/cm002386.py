def build_composite_models(config_class, output_dir):
    import tempfile

    from transformers import (
        BertConfig,
        BertLMHeadModel,
        BertModel,
        BertTokenizer,
        BertTokenizerFast,
        EncoderDecoderModel,
        GPT2Config,
        GPT2LMHeadModel,
        GPT2Tokenizer,
        GPT2TokenizerFast,
        SpeechEncoderDecoderModel,
        VisionEncoderDecoderModel,
        VisionTextDualEncoderModel,
        ViTConfig,
        ViTModel,
        Wav2Vec2Config,
        Wav2Vec2Model,
        Wav2Vec2Processor,
    )

    # These will be removed at the end if they are empty
    result = {"error": None, "warnings": []}

    if config_class.model_type == "encoder-decoder":
        encoder_config_class = BertConfig
        decoder_config_class = BertConfig
        encoder_processor = (BertTokenizerFast, BertTokenizer)
        decoder_processor = (BertTokenizerFast, BertTokenizer)
        encoder_class = BertModel
        decoder_class = BertLMHeadModel
        model_class = EncoderDecoderModel
    elif config_class.model_type == "vision-encoder-decoder":
        encoder_config_class = ViTConfig
        decoder_config_class = GPT2Config
        encoder_processor = (ViTImageProcessor,)
        decoder_processor = (GPT2TokenizerFast, GPT2Tokenizer)
        encoder_class = ViTModel
        decoder_class = GPT2LMHeadModel
        model_class = VisionEncoderDecoderModel
    elif config_class.model_type == "speech-encoder-decoder":
        encoder_config_class = Wav2Vec2Config
        decoder_config_class = BertConfig
        encoder_processor = (Wav2Vec2Processor,)
        decoder_processor = (BertTokenizerFast, BertTokenizer)
        encoder_class = Wav2Vec2Model
        decoder_class = BertLMHeadModel
        model_class = SpeechEncoderDecoderModel
    elif config_class.model_type == "vision-text-dual-encoder":
        # Not encoder-decoder, but encoder-encoder. We just keep the same name as above to make code easier
        encoder_config_class = ViTConfig
        decoder_config_class = BertConfig
        encoder_processor = (ViTImageProcessor,)
        decoder_processor = (BertTokenizerFast, BertTokenizer)
        encoder_class = ViTModel
        decoder_class = BertModel
        model_class = VisionTextDualEncoderModel

    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            # build encoder
            models_to_create = {"processor": encoder_processor, "pytorch": (encoder_class,)}
            encoder_output_dir = os.path.join(tmpdir, "encoder")
            build(encoder_config_class, models_to_create, encoder_output_dir, keep_model=True)

            # build decoder
            models_to_create = {"processor": decoder_processor, "pytorch": (decoder_class,)}
            decoder_output_dir = os.path.join(tmpdir, "decoder")
            build(decoder_config_class, models_to_create, decoder_output_dir, keep_model=True)

            # build encoder-decoder
            encoder_path = os.path.join(encoder_output_dir, encoder_class.__name__)
            decoder_path = os.path.join(decoder_output_dir, decoder_class.__name__)

            if config_class.model_type != "vision-text-dual-encoder":
                # Specify these explicitly for encoder-decoder like models, but not for `vision-text-dual-encoder` as it
                # has no decoder.
                decoder_config = decoder_config_class.from_pretrained(decoder_path)
                decoder_config.is_decoder = True
                decoder_config.add_cross_attention = True
                model = model_class.from_encoder_decoder_pretrained(
                    encoder_path,
                    decoder_path,
                    decoder_config=decoder_config,
                )
            elif config_class.model_type == "vision-text-dual-encoder":
                model = model_class.from_vision_text_pretrained(encoder_path, decoder_path)

            model_path = os.path.join(
                output_dir,
                f"{model_class.__name__}-{encoder_config_class.model_type}-{decoder_config_class.model_type}",
            )
            model.save_pretrained(model_path)

            # copy the processors
            encoder_processor_path = os.path.join(encoder_output_dir, "processors")
            decoder_processor_path = os.path.join(decoder_output_dir, "processors")
            if os.path.isdir(encoder_processor_path):
                shutil.copytree(encoder_processor_path, model_path, dirs_exist_ok=True)
            if os.path.isdir(decoder_processor_path):
                shutil.copytree(decoder_processor_path, model_path, dirs_exist_ok=True)

            # fill `result`
            result["processor"] = {x.__name__: x.__name__ for x in encoder_processor + decoder_processor}

            result["pytorch"] = {model_class.__name__: {"model": model_class.__name__, "checkpoint": model_path}}

        except Exception:
            result["error"] = (
                f"Failed to build models for {config_class.__name__}.",
                traceback.format_exc(),
            )

    if not result["error"]:
        del result["error"]
    if not result["warnings"]:
        del result["warnings"]

    return result