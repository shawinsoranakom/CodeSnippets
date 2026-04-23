def convert_checkpoint(
    pytorch_dump_folder_path,
    checkpoint_path=None,
    config_path=None,
    vocab_path=None,
    language=None,
    num_speakers=None,
    sampling_rate=None,
    repo_id=None,
):
    """
    Copy/paste/tweak model's weights to transformers design.
    """
    if config_path is not None:
        config = VitsConfig.from_pretrained(config_path)
    else:
        config = VitsConfig()

    if num_speakers:
        config.num_speakers = num_speakers
        config.speaker_embedding_size = 256

    if sampling_rate:
        config.sampling_rate = sampling_rate

    if checkpoint_path is None:
        logger.info(f"***Converting model: facebook/mms-tts {language}***")

        vocab_path = hf_hub_download(
            repo_id="facebook/mms-tts",
            filename="vocab.txt",
            subfolder=f"models/{language}",
        )
        config_file = hf_hub_download(
            repo_id="facebook/mms-tts",
            filename="config.json",
            subfolder=f"models/{language}",
        )
        checkpoint_path = hf_hub_download(
            repo_id="facebook/mms-tts",
            filename="G_100000.pth",
            subfolder=f"models/{language}",
        )

        with open(config_file, "r") as f:
            data = f.read()
            hps = json.loads(data)

        is_uroman = hps["data"]["training_files"].split(".")[-1] == "uroman"
        if is_uroman:
            logger.warning("For this checkpoint, you should use `uroman` to convert input text before tokenizing it!")
    else:
        logger.info(f"***Converting model: {checkpoint_path}***")
        is_uroman = False

    # original VITS checkpoint
    if vocab_path is None:
        _pad = "_"
        _punctuation = ';:,.!?¡¿—…"«»“” '
        _letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
        _letters_ipa = "ɑɐɒæɓʙβɔɕçɗɖðʤəɘɚɛɜɝɞɟʄɡɠɢʛɦɧħɥʜɨɪʝɭɬɫɮʟɱɯɰŋɳɲɴøɵɸθœɶʘɹɺɾɻʀʁɽʂʃʈʧʉʊʋⱱʌɣɤʍχʎʏʑʐʒʔʡʕʢǀǁǂǃˈˌːˑʼʴʰʱʲʷˠˤ˞↓↑→↗↘'̩'ᵻ"
        symbols = _pad + _punctuation + _letters + _letters_ipa
        symbol_to_id = {s: i for i, s in enumerate(symbols)}
        phonemize = True
    else:
        # Save vocab as temporary json file
        symbols = [line.replace("\n", "") for line in open(vocab_path, encoding="utf-8")]
        symbol_to_id = {s: i for i, s in enumerate(symbols)}
        # MMS-TTS does not use a <pad> token, so we set to the token used to space characters
        _pad = symbols[0]
        phonemize = False

    with tempfile.NamedTemporaryFile() as tf:
        with open(tf.name, "w", encoding="utf-8") as f:
            f.write(json.dumps(symbol_to_id, indent=2, sort_keys=True, ensure_ascii=False) + "\n")

        tokenizer = VitsTokenizer(tf.name, language=language, phonemize=phonemize, is_uroman=is_uroman, pad_token=_pad)

    config.vocab_size = len(symbols)
    model = VitsModel(config)

    model.decoder.apply_weight_norm()

    orig_checkpoint = torch.load(checkpoint_path, map_location=torch.device("cpu"), weights_only=True)
    recursively_load_weights(orig_checkpoint["model"], model)

    model.decoder.remove_weight_norm()

    model.save_pretrained(pytorch_dump_folder_path)
    tokenizer.save_pretrained(pytorch_dump_folder_path)

    if repo_id:
        print("Pushing to the hub...")
        tokenizer.push_to_hub(repo_id)
        model.push_to_hub(repo_id)