def __init__(
        self,
        tags_dict,
        vocab: str | dict[str, int] | list[tuple[str, float]] | None = None,
        merges: str | list[str] | None = None,
        errors="replace",
        bos_token="<s>",
        eos_token="</s>",
        sep_token="</s>",
        cls_token="<s>",
        unk_token="<unk>",
        pad_token="<pad>",
        mask_token="<mask>",
        add_prefix_space=False,
        max_depth=50,
        max_width=1000,
        pad_width=1001,
        pad_token_label=-100,
        only_label_first_subword=True,
        trim_offsets=False,
        **kwargs,
    ):
        bos_token = AddedToken(bos_token, lstrip=False, rstrip=False) if isinstance(bos_token, str) else bos_token
        eos_token = AddedToken(eos_token, lstrip=False, rstrip=False) if isinstance(eos_token, str) else eos_token
        sep_token = AddedToken(sep_token, lstrip=False, rstrip=False) if isinstance(sep_token, str) else sep_token
        cls_token = AddedToken(cls_token, lstrip=False, rstrip=False) if isinstance(cls_token, str) else cls_token
        unk_token = AddedToken(unk_token, lstrip=False, rstrip=False) if isinstance(unk_token, str) else unk_token
        pad_token = AddedToken(pad_token, lstrip=False, rstrip=False) if isinstance(pad_token, str) else pad_token
        # Mask token behave like a normal word, i.e. include the space before it
        mask_token = AddedToken(mask_token, lstrip=True, rstrip=False) if isinstance(mask_token, str) else mask_token

        if vocab is None:
            vocab = {
                str(pad_token): 0,
                str(unk_token): 1,
                str(cls_token): 2,
                str(sep_token): 3,
                str(mask_token): 4,
            }
        merges = merges or []
        tokenizer = Tokenizer(
            BPE(
                vocab=vocab,
                merges=merges,
                dropout=None,
                continuing_subword_prefix="",
                end_of_word_suffix="",
                fuse_unk=False,
            )
        )
        tokenizer.pre_tokenizer = pre_tokenizers.ByteLevel(add_prefix_space=add_prefix_space)
        tokenizer.decoder = decoders.ByteLevel()
        self._vocab = vocab
        self._merges = merges
        self._tokenizer = tokenizer
        super().__init__(
            tags_dict=tags_dict,
            errors=errors,
            bos_token=bos_token,
            eos_token=eos_token,
            unk_token=unk_token,
            sep_token=sep_token,
            cls_token=cls_token,
            pad_token=pad_token,
            mask_token=mask_token,
            add_prefix_space=add_prefix_space,
            trim_offsets=trim_offsets,
            max_depth=max_depth,
            max_width=max_width,
            pad_width=pad_width,
            pad_token_label=pad_token_label,
            only_label_first_subword=only_label_first_subword,
            **kwargs,
        )
        sep_token_str = str(sep_token)
        cls_token_str = str(cls_token)
        cls_token_id = self.cls_token_id
        sep_token_id = self.sep_token_id
        self._tokenizer.post_processor = processors.TemplateProcessing(
            single=f"{cls_token_str} $A {sep_token_str}",
            pair=f"{cls_token_str} $A {sep_token_str} $B {sep_token_str}",
            special_tokens=[
                (cls_token_str, cls_token_id),
                (sep_token_str, sep_token_id),
            ],
        )

        self.tags_dict = tags_dict

        # additional properties
        self.max_depth = max_depth
        self.max_width = max_width
        self.pad_width = pad_width
        self.unk_tag_id = len(self.tags_dict)
        self.pad_tag_id = self.unk_tag_id + 1
        self.pad_xpath_tags_seq = [self.pad_tag_id] * self.max_depth
        self.pad_xpath_subs_seq = [self.pad_width] * self.max_depth
        self.pad_token_label = pad_token_label
        self.only_label_first_subword = only_label_first_subword