def _preserve_sentencepiece_tokenizer_assets(
    tokenizer,
    save_directory,
    token = None,
):
    tokenizer = tokenizer.tokenizer if hasattr(tokenizer, "tokenizer") else tokenizer
    if tokenizer is None or not os.path.isdir(save_directory):
        return

    tokenizer_config_path = os.path.join(save_directory, "tokenizer_config.json")
    if os.path.isfile(tokenizer_config_path):
        desired_added_tokens_decoder = {}
        for token_id, added_token in getattr(
            tokenizer, "added_tokens_decoder", {}
        ).items():
            desired_added_tokens_decoder[str(token_id)] = {
                "content": getattr(added_token, "content", str(added_token)),
                "single_word": getattr(added_token, "single_word", False),
                "lstrip": getattr(added_token, "lstrip", False),
                "rstrip": getattr(added_token, "rstrip", False),
                "normalized": getattr(added_token, "normalized", True),
                "special": getattr(added_token, "special", False),
            }
        if desired_added_tokens_decoder:
            with open(tokenizer_config_path, "r", encoding = "utf-8") as file:
                tokenizer_config = json.load(file)
            if (
                tokenizer_config.get("added_tokens_decoder")
                != desired_added_tokens_decoder
            ):
                tokenizer_config["added_tokens_decoder"] = desired_added_tokens_decoder
                with open(tokenizer_config_path, "w", encoding = "utf-8") as file:
                    json.dump(tokenizer_config, file, indent = 2, ensure_ascii = False)
                    file.write("\n")
                logger.warning_once(
                    f"Unsloth: Restored added_tokens_decoder metadata in "
                    f"{tokenizer_config_path}."
                )

    tokenizer_model = os.path.join(save_directory, "tokenizer.model")
    downloaded_path = None
    if not os.path.isfile(tokenizer_model) and _has_tokenizer_model(
        tokenizer,
        token = token,
    ):
        source = getattr(tokenizer, "name_or_path", None)
        if isinstance(source, str) and source:
            if os.path.isdir(source):
                local_path = os.path.join(source, "tokenizer.model")
                if os.path.isfile(local_path):
                    downloaded_path = local_path
            else:
                from huggingface_hub import hf_hub_download

                try:
                    downloaded_path = hf_hub_download(
                        repo_id = source,
                        filename = "tokenizer.model",
                        token = token,
                    )
                except Exception:
                    downloaded_path = None

    if not os.path.isfile(tokenizer_model) and downloaded_path is not None:
        shutil.copy2(downloaded_path, tokenizer_model)
        logger.warning_once(
            f"Unsloth: Preserved sentencepiece asset `tokenizer.model` in "
            f"{save_directory}."
        )