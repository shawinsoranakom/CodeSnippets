def __init__(
        self,
        model_dir: str = "G2PWModel/",
        style: str = "bopomofo",
        model_source: str = None,
        enable_non_tradional_chinese: bool = False,
    ):
        self.model_dir = download_and_decompress(model_dir)
        self.config = load_config(config_path=os.path.join(self.model_dir, "config.py"), use_default=True)

        self.model_source = model_source if model_source else self.config.model_source
        self.enable_opencc = enable_non_tradional_chinese
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_source)

        polyphonic_chars_path = os.path.join(self.model_dir, "POLYPHONIC_CHARS.txt")
        monophonic_chars_path = os.path.join(self.model_dir, "MONOPHONIC_CHARS.txt")

        self.polyphonic_chars = [
            line.split("\t") for line in open(polyphonic_chars_path, encoding="utf-8").read().strip().split("\n")
        ]
        self.non_polyphonic = {
            "一",
            "不",
            "和",
            "咋",
            "嗲",
            "剖",
            "差",
            "攢",
            "倒",
            "難",
            "奔",
            "勁",
            "拗",
            "肖",
            "瘙",
            "誒",
            "泊",
            "听",
            "噢",
        }
        self.non_monophonic = {"似", "攢"}
        self.monophonic_chars = [
            line.split("\t") for line in open(monophonic_chars_path, encoding="utf-8").read().strip().split("\n")
        ]
        self.labels, self.char2phonemes = (
            get_char_phoneme_labels(polyphonic_chars=self.polyphonic_chars)
            if self.config.use_char_phoneme
            else get_phoneme_labels(polyphonic_chars=self.polyphonic_chars)
        )

        self.chars = sorted(list(self.char2phonemes.keys()))
        self.char2id = {char: idx for idx, char in enumerate(self.chars)}
        self.char_phoneme_masks = (
            {
                char: [1 if i in self.char2phonemes[char] else 0 for i in range(len(self.labels))]
                for char in self.char2phonemes
            }
            if self.config.use_mask
            else None
        )

        self.polyphonic_chars_new = set(self.chars)
        for char in self.non_polyphonic:
            self.polyphonic_chars_new.discard(char)

        self.monophonic_chars_dict = {char: phoneme for char, phoneme in self.monophonic_chars}
        for char in self.non_monophonic:
            self.monophonic_chars_dict.pop(char, None)

        default_asset_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "G2PWModel"))
        candidate_asset_dirs = [self.model_dir, default_asset_dir]
        self.bopomofo_convert_dict = _load_json_from_candidates(
            "bopomofo_to_pinyin_wo_tune_dict.json", candidate_asset_dirs
        )
        self.char_bopomofo_dict = _load_json_from_candidates("char_bopomofo_dict.json", candidate_asset_dirs)

        self.style_convert_func = {
            "bopomofo": lambda x: x,
            "pinyin": self._convert_bopomofo_to_pinyin,
        }[style]

        if self.enable_opencc:
            self.cc = OpenCC("s2tw")
        self.enable_sentence_dedup = os.getenv("g2pw_sentence_dedup", "true").strip().lower() in {
            "1",
            "true",
            "yes",
            "y",
            "on",
        }
        # 聚焦到多音字附近上下文，默认左右各16字；设为0表示关闭裁剪（整句）。
        self.polyphonic_context_chars = max(0, int(os.getenv("g2pw_polyphonic_context_chars", "16")))