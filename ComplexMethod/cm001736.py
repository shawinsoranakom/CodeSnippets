def setUpClass(cls) -> None:
        # Tokenizer.filter makes it possible to filter which Tokenizer to case based on all the
        # information available in Tokenizer (name, tokenizer class, vocab key name)
        if cls.from_pretrained_id is None:
            cls.from_pretrained_id = []
        elif isinstance(cls.from_pretrained_id, str):
            cls.from_pretrained_id = [cls.from_pretrained_id]

        cls.tokenizers_list = []
        if cls.tokenizer_class is not None:
            cls.tokenizers_list = [
                (
                    cls.tokenizer_class,
                    pretrained_id,
                    cls.from_pretrained_kwargs if cls.from_pretrained_kwargs is not None else {},
                )
                for pretrained_id in cls.from_pretrained_id
            ]
        with open(f"{get_tests_dir()}/fixtures/sample_text.txt", encoding="utf-8") as f_data:
            cls._data = f_data.read().replace("\n\n", "\n").strip()

        cls.tmpdirname = tempfile.mkdtemp()

        # save the first pretrained tokenizer to tmpdirname for tests to use
        if cls.from_pretrained_id and cls.tokenizer_class is not None:
            tokenizer = AutoTokenizer.from_pretrained(
                cls.from_pretrained_id[0],
                **(cls.from_pretrained_kwargs if cls.from_pretrained_kwargs is not None else {}),
            )
            tokenizer.save_pretrained(cls.tmpdirname)