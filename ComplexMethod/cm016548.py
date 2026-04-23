def __init__(self, tokenizer_path=None, max_length=77, pad_with_end=True, embedding_directory=None, embedding_size=768, embedding_key='clip_l', tokenizer_class=CLIPTokenizer, has_start_token=True, has_end_token=True, pad_to_max_length=True, min_length=None, pad_token=None, end_token=None, start_token=None, min_padding=None, pad_left=False, disable_weights=False, tokenizer_data={}, tokenizer_args={}):
        if tokenizer_path is None:
            tokenizer_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "sd1_tokenizer")
        self.tokenizer = tokenizer_class.from_pretrained(tokenizer_path, **tokenizer_args)
        self.max_length = tokenizer_data.get("{}_max_length".format(embedding_key), max_length)
        self.min_length = tokenizer_data.get("{}_min_length".format(embedding_key), min_length)
        self.end_token = None
        self.min_padding = min_padding
        self.pad_left = pad_left

        empty = self.tokenizer('')["input_ids"]
        self.tokenizer_adds_end_token = has_end_token
        if has_start_token:
            if len(empty) > 0:
                self.tokens_start = 1
                self.start_token = empty[0]
            else:
                self.tokens_start = 0
                self.start_token = start_token
                if start_token is None:
                    logging.warning("WARNING: There's something wrong with your tokenizers.'")

            if end_token is not None:
                self.end_token = end_token
            else:
                if has_end_token:
                    self.end_token = empty[1]
        else:
            self.tokens_start = 0
            self.start_token = start_token
            if end_token is not None:
                self.end_token = end_token
            else:
                if has_end_token:
                    self.end_token = empty[0]

        if pad_token is not None:
            self.pad_token = pad_token
        elif pad_with_end:
            self.pad_token = self.end_token
        else:
            self.pad_token = 0

        self.pad_with_end = pad_with_end
        self.pad_to_max_length = pad_to_max_length

        vocab = self.tokenizer.get_vocab()
        self.inv_vocab = {v: k for k, v in vocab.items()}
        self.embedding_directory = embedding_directory
        self.max_word_length = 8
        self.embedding_identifier = "embedding:"
        self.embedding_size = embedding_size
        self.embedding_key = embedding_key

        self.disable_weights = disable_weights