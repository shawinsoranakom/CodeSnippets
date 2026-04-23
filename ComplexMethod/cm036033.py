def __init__(self, path: PurePath, tokenizer: Callable, train: str, valid: str, test: str, *,
                 n_tokens: Optional[int] = None,
                 stoi: Optional[Dict[str, int]] = None,
                 itos: Optional[List[str]] = None):
        self.test = test
        self.valid = valid
        self.train = train
        self.tokenizer = tokenizer
        self.path = path

        if n_tokens or stoi or itos:
            assert stoi and itos and n_tokens
            self.n_tokens = n_tokens
            self.stoi = stoi
            self.itos = itos
        else:
            self.n_tokens = len(self.standard_tokens)
            self.stoi = {t: i for i, t in enumerate(self.standard_tokens)}

            with monit.section("Tokenize"):
                tokens = self.tokenizer(self.train) + self.tokenizer(self.valid)
                tokens = sorted(list(set(tokens)))

            for t in monit.iterate("Build vocabulary", tokens):
                self.stoi[t] = self.n_tokens
                self.n_tokens += 1

            self.itos = [''] * self.n_tokens
            for t, n in self.stoi.items():
                self.itos[n] = t