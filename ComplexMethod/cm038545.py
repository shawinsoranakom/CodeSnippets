def _load_tiktoken_encoding(
    vocab_file: Path,
) -> tuple[Any, dict[str, int]]:
    try:
        import tiktoken
    except ImportError as exc:
        raise ImportError("Grok-2 tokenizer requires the `tiktoken` package.") from exc

    with vocab_file.open("rb") as f:
        xtok_dict = json.load(f)

    mergeable_ranks = {
        bytes(item["bytes"]): item["token"]
        for item in xtok_dict.get("regular_tokens", [])
    }
    special_tokens = {
        bytes(item["bytes"]).decode("utf-8", errors="replace"): item["token"]
        for item in xtok_dict.get("special_tokens", [])
    }

    if xtok_dict.get("word_split") == "V1":
        pat_str = PAT_STR_B
    else:
        raise ValueError(f"Unknown word_split: {xtok_dict.get('word_split')!r}")

    pat_str = xtok_dict.get("pat_str", pat_str)

    kwargs = {
        "name": str(vocab_file),
        "pat_str": pat_str,
        "mergeable_ranks": mergeable_ranks,
        "special_tokens": special_tokens,
    }

    if "vocab_size" in xtok_dict:
        kwargs["explicit_n_vocab"] = xtok_dict["vocab_size"]

    tokenizer = tiktoken.Encoding(**kwargs)

    default_allowed_special: set[str] | None = None
    if "default_allowed_special" in xtok_dict:
        default_allowed_special = {
            bytes(bytes_list).decode("utf-8", errors="replace")
            for bytes_list in xtok_dict["default_allowed_special"]
        }

    tokenizer._default_allowed_special = default_allowed_special or set()
    tokenizer._control_tokens = DEFAULT_CONTROL_TOKENS

    def encode_patched(
        self,
        text: str,
        *,
        allowed_special: Literal["all"] | Set[str] = set(),
        disallowed_special: Literal["all"] | Collection[str] = "all",
    ) -> list[int]:
        del disallowed_special
        if isinstance(allowed_special, set):
            allowed_special |= self._default_allowed_special
        return tiktoken.Encoding.encode(
            self,
            text,
            allowed_special=allowed_special,
            disallowed_special=(),
        )

    tokenizer.encode = functools.partial(encode_patched, tokenizer)
    tokenizer._default_allowed_special |= set(DEFAULT_CONTROL_TOKENS.values())
    tokenizer._default_allowed_special |= set(
        CONTROL_TOKEN_TEXTS + RESERVED_TOKEN_TEXTS
    )

    return tokenizer, special_tokens