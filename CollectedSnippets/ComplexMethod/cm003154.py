def load_model(save_dir, model_type, repo_id):
    """
    Meta SeamlessM4T is made of 8 main components:
    - speech_encoder (#1) and speech_encoder_frontend (#2)
    - t2u_model (#3)
    - text_encoder (#4) and text_encoder_frontend (#5)
    - text_decoder (#6) [and text_decoder_frontend (#5) = equals to text_encoder_frontend]
    - final_proj (#7)
    - vocoder (#8)
    """
    device = _grab_best_device()
    if model_type == "medium":
        name = "seamlessM4T_medium"
    else:
        name = "seamlessM4T_large"

    original_model = Translator(name, "vocoder_36langs", device, torch.float32)

    ######### TOKENIZER

    langs = MEDIUM_SUPPORTED_LANGUAGES if model_type == "medium" else LARGE_SUPPORTED_LANGUAGES
    langs = [f"__{lang}__" for lang in langs]
    vocab_file = os.path.join(os.path.expanduser("~"), "tokenizer", model_type, "tokenizer.model")

    save_dir = os.path.join(save_dir, name)
    Path(save_dir).mkdir(exist_ok=True)

    tokenizer = SeamlessM4TTokenizer(vocab_file, additional_special_tokens=langs)

    sanity_check_lang_id = tokenizer.convert_tokens_to_ids("__fra__")

    tokenizer.save_pretrained(save_dir)
    tokenizer = SeamlessM4TTokenizer.from_pretrained(save_dir)

    if sanity_check_lang_id != tokenizer.convert_tokens_to_ids("__fra__"):
        raise ValueError(
            f"Error in tokenizer saving/loading - __fra__ lang id is not coherent: {sanity_check_lang_id} vs {tokenizer.convert_tokens_to_ids('__fra__')}"
        )

    ####### get language to ids dict
    text_decoder_lang_code_to_id = {lang.replace("__", ""): tokenizer.convert_tokens_to_ids(lang) for lang in langs}
    # offset: vocoder unit vocab size + 5 (for EOS/PAD/BOS/UNK/MSK) + len(supported_languages)
    t2u_lang_code_to_id = {
        code.replace("__", ""): i + 10005 + len(UNIT_SUPPORTED_LANGUAGES)
        for i, code in enumerate(UNIT_SUPPORTED_LANGUAGES)
    }
    vocoder_lang_code_to_id = {code.replace("__", ""): i for i, code in enumerate(VOCODER_SUPPORTED_LANGUAGES)}

    ######### FE

    fe = SeamlessM4TFeatureExtractor(language_code=langs)

    fe.save_pretrained(save_dir)
    fe = SeamlessM4TFeatureExtractor.from_pretrained(save_dir)

    processor = SeamlessM4TProcessor(feature_extractor=fe, tokenizer=tokenizer)
    processor.save_pretrained(save_dir)
    processor.push_to_hub(repo_id=repo_id, create_pr=True)

    processor = SeamlessM4TProcessor.from_pretrained(save_dir)

    ######## Model

    # init model
    hf_config = _load_hf_config(model_type)
    hf_model = SeamlessM4TModel(hf_config)

    hf_model.generation_config.__setattr__("text_decoder_lang_to_code_id", text_decoder_lang_code_to_id)
    hf_model.generation_config.__setattr__("t2u_lang_code_to_id", t2u_lang_code_to_id)
    hf_model.generation_config.__setattr__("vocoder_lang_code_to_id", vocoder_lang_code_to_id)

    # -1. take care of vocoder
    # similarly to speech T5 must apply and remove weight norm
    hf_model.vocoder.apply_weight_norm()
    hf_model.vocoder = _convert_model(
        original_model,
        hf_model.vocoder,
        vocoder_convert_list,
        device,
        unwanted_prefix="vocoder.code_generator.",
        filter_state_dict="vocoder",
    )
    hf_model.vocoder.remove_weight_norm()

    # 1. take care of speech encoder
    wav2vec = hf_model.speech_encoder
    hf_model.speech_encoder = _convert_model(
        original_model, wav2vec, wav2vec_convert_list, device, unwanted_prefix="model.", filter_state_dict="speech"
    )

    # 2. take care of t2u

    hf_model.t2u_model = _convert_model(
        original_model,
        hf_model.t2u_model,
        t2u_convert_list,
        device,
        unwanted_prefix="model.",
        filter_state_dict="t2u_model",
    )

    # 3. take care of text encoder
    hf_model.text_encoder = _convert_model(
        original_model,
        hf_model.text_encoder,
        text_convert_list,
        device,
        unwanted_prefix="model.",
        filter_state_dict=["model.text_encoder"],
        exclude_state_dict="t2u_model",
    )

    # 4. take care of text decoder
    hf_model.text_decoder = _convert_model(
        original_model,
        hf_model.text_decoder,
        text_convert_list,
        device,
        unwanted_prefix="model.",
        filter_state_dict=["model.text_decoder"],
        exclude_state_dict="t2u_model",
    )

    # 5. take care of final proj
    hf_model.lm_head = _convert_model(
        original_model,
        hf_model.lm_head,
        [("final_proj.", "")],
        device,
        unwanted_prefix="model.",
        filter_state_dict=["model.final_proj"],
        exclude_state_dict="t2u_model",
    )

    # sanity check
    print(find_tied_parameters(hf_model))

    count_1 = param_count(hf_model)
    count_2 = param_count(original_model)

    print(f"HF MODEL:{count_1}, ORIGINAL_MODEL: {count_2}, diff:{count_1 - count_2}")
    print(f"HF MODEL excluding embeddings:{hf_model.num_parameters(exclude_embeddings=True)}")

    del original_model

    hf_model.generation_config._from_model_config = False
    hf_model.save_pretrained(save_dir)
    hf_model.push_to_hub(repo_id=repo_id, create_pr=True)
    hf_model = SeamlessM4TModel.from_pretrained(save_dir)