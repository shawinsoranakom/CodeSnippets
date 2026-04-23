def from_pretrained(
        cls,
        path_or_repo_id: str | Path,
        *args,
        trust_remote_code: bool = False,
        revision: str | None = None,
        download_dir: str | None = None,
        **kwargs,
    ) -> "KimiAudioTokenizer":
        if args:
            logger.debug_once("Ignoring extra positional args for KimiAudioTokenizer.")

        path = Path(path_or_repo_id)
        if path.is_file():
            vocab_file = path
        elif path.is_dir():
            vocab_file = path / "tiktoken.model"
            if not vocab_file.is_file():
                vocab_file = path / "tokenizer.model"
        else:
            # Download from HuggingFace Hub
            repo_id = str(path_or_repo_id)

            # Try to download tiktoken.model or tokenizer.model
            try:
                vocab_path = hf_hub_download(
                    repo_id=repo_id,
                    filename="tiktoken.model",
                    revision=revision,
                    local_dir=download_dir,
                )
                vocab_file = Path(vocab_path)
            except Exception:
                try:
                    vocab_path = hf_hub_download(
                        repo_id=repo_id,
                        filename="tokenizer.model",
                        revision=revision,
                        local_dir=download_dir,
                    )
                    vocab_file = Path(vocab_path)
                except Exception as exc:
                    raise ValueError(
                        f"Could not find tiktoken.model or tokenizer.model in {repo_id}"
                    ) from exc

            # Also download tokenizer_config.json if available
            with contextlib.suppress(Exception):
                hf_hub_download(
                    repo_id=repo_id,
                    filename="tokenizer_config.json",
                    revision=revision,
                    local_dir=download_dir,
                )

        if not vocab_file.is_file():
            raise FileNotFoundError(f"tiktoken.model not found at {vocab_file}.")

        return cls(
            vocab_file=vocab_file,
            name_or_path=str(path_or_repo_id),
            truncation_side=kwargs.get("truncation_side", "left"),
        )