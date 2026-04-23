def download_model(model_size: str):
    url = "https://huggingface.co/api/models/gpt2"
    try:
        requests.get(url, timeout=3)
        source = "HF"
    except Exception:
        source = "ModelScope"

    model_path = ""
    if source == "HF":
        if "distil" in model_size:
            if "3.5" in model_size:
                repo_id = "distil-whisper/distil-large-v3.5-ct2"
                model_path = "tools/asr/models/faster-distil-whisper-large-v3.5"
            else:
                repo_id = "Systran/faster-{}-whisper-{}".format(*model_size.split("-", maxsplit=1))
        elif model_size == "large-v3-turbo":
            repo_id = "mobiuslabsgmbh/faster-whisper-large-v3-turbo"
            model_path = "tools/asr/models/faster-whisper-large-v3-turbo"
        else:
            repo_id = f"Systran/faster-whisper-{model_size}"
        model_path = (
            model_path or f"tools/asr/models/{repo_id.replace('Systran/', '').replace('distil-whisper/', '', 1)}"
        )
    else:
        repo_id = "XXXXRT/faster-whisper"
        model_path = "tools/asr/models"

    files: list[str] = [
        "config.json",
        "model.bin",
        "tokenizer.json",
        "vocabulary.txt",
    ]
    if "large-v3" in model_size or "distil" in model_size:
        files.append("preprocessor_config.json")
        files.append("vocabulary.json")

        files.remove("vocabulary.txt")

    if source == "ModelScope":
        files = [f"faster-whisper-{model_size}/{file}".replace("whisper-distil", "distil-whisper") for file in files]

    if source == "HF":
        print(f"Downloading model from HuggingFace: {repo_id} to {model_path}")
        snapshot_download_hf(
            repo_id,
            local_dir=model_path,
            local_dir_use_symlinks=False,
            allow_patterns=files,
        )
    else:
        print(f"Downloading model from ModelScope: {repo_id} to {model_path}")
        snapshot_download_ms(
            repo_id,
            local_dir=model_path,
            allow_patterns=files,
        )
        return model_path + f"/faster-whisper-{model_size}".replace("whisper-distil", "distil-whisper")
    return model_path