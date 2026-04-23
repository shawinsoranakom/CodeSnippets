def setUpClass(cls) -> None:
        cls.from_pretrained_id = (
            [cls.from_pretrained_id] if isinstance(cls.from_pretrained_id, str) else cls.from_pretrained_id
        )
        # Use rust_tokenizer_class if set, otherwise fall back to tokenizer_class
        tokenizer_class = getattr(cls, "rust_tokenizer_class", None) or getattr(cls, "tokenizer_class", None)
        cls.tokenizers_list = [
            (
                tokenizer_class,
                pretrained_id,
                cls.from_pretrained_kwargs if cls.from_pretrained_kwargs is not None else {},
            )
            for pretrained_id in (cls.from_pretrained_id or [])
        ]
        cls.tmpdirname = tempfile.mkdtemp()

        # save the first pretrained tokenizer to tmpdirname for tests to use
        if cls.from_pretrained_id and tokenizer_class is not None:
            try:
                from transformers import AutoTokenizer

                tokenizer = AutoTokenizer.from_pretrained(
                    cls.from_pretrained_id[0],
                    **(cls.from_pretrained_kwargs if cls.from_pretrained_kwargs is not None else {}),
                )
                tokenizer.save_pretrained(cls.tmpdirname)
            except Exception as e:
                print(f"Could not setup tokenizer: {e}")