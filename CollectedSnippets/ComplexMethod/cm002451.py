def load_vocab_and_merges(pretrained_model_name_or_path, **kwargs):
    """
    Resolve and load tokenizer vocabulary files from a repo/path.

    Priority order:
    1. Load ``vocab.json`` (WordLevel/WordPiece/BPE fast tokenizers)
    2. Load ``vocab.txt`` when only a WordPiece vocab is available
    3. Optionally load ``merges.txt`` (BPE tokenizers)

    Returns:
        tuple (vocab: dict|None, merges: list[tuple[str,str]]|None, files_loaded: list[str])
    """
    files_loaded = []
    vocab = None
    merges = None
    try:
        resolved_vocab_file = cached_file(
            pretrained_model_name_or_path,
            "vocab.json",
            cache_dir=kwargs.get("cache_dir"),
            force_download=kwargs.get("force_download", False),
            proxies=kwargs.get("proxies"),
            token=kwargs.get("token"),
            revision=kwargs.get("revision"),
            local_files_only=kwargs.get("local_files_only", False),
            subfolder=kwargs.get("subfolder", ""),
        )
    except Exception:
        resolved_vocab_file = None

    if resolved_vocab_file is not None:
        try:
            with open(resolved_vocab_file, "r", encoding="utf-8") as vf:
                vocab = json.load(vf)
            files_loaded.append("vocab.json")
        except Exception:
            vocab = None

    # Fallback to vocab.txt (WordPiece-style vocabularies)
    if vocab is None:
        try:
            resolved_vocab_txt = cached_file(
                pretrained_model_name_or_path,
                "vocab.txt",
                cache_dir=kwargs.get("cache_dir"),
                force_download=kwargs.get("force_download", False),
                proxies=kwargs.get("proxies"),
                token=kwargs.get("token"),
                revision=kwargs.get("revision"),
                local_files_only=kwargs.get("local_files_only", False),
                subfolder=kwargs.get("subfolder", ""),
            )
        except Exception:
            resolved_vocab_txt = None

        if resolved_vocab_txt is not None:
            try:
                vocab = OrderedDict()
                with open(resolved_vocab_txt, "r", encoding="utf-8") as vf:
                    for index, token in enumerate(vf):
                        token = token.rstrip("\n")
                        vocab[token] = index
                files_loaded.append("vocab.txt")
            except Exception:
                vocab = None

    try:
        resolved_merges_file = cached_file(
            pretrained_model_name_or_path,
            "merges.txt",
            cache_dir=kwargs.get("cache_dir"),
            force_download=kwargs.get("force_download", False),
            proxies=kwargs.get("proxies"),
            token=kwargs.get("token"),
            revision=kwargs.get("revision"),
            local_files_only=kwargs.get("local_files_only", False),
            subfolder=kwargs.get("subfolder", ""),
        )
    except Exception:
        resolved_merges_file = None

    if resolved_merges_file is not None:
        try:
            merges = []
            with open(resolved_merges_file, "r", encoding="utf-8") as mf:
                for line in mf:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        parts = line.split()
                        if len(parts) == 2:
                            merges.append((parts[0], parts[1]))
            files_loaded.append("merges.txt")
        except Exception:
            merges = None

    return vocab, merges, files_loaded