def __init__(self, wrapped, hijack):
        super().__init__(wrapped, hijack)
        self.tokenizer = wrapped.tokenizer

        vocab = self.tokenizer.get_vocab()

        self.comma_token = vocab.get(',</w>', None)

        self.token_mults = {}
        tokens_with_parens = [(k, v) for k, v in vocab.items() if '(' in k or ')' in k or '[' in k or ']' in k]
        for text, ident in tokens_with_parens:
            mult = 1.0
            for c in text:
                if c == '[':
                    mult /= 1.1
                if c == ']':
                    mult *= 1.1
                if c == '(':
                    mult *= 1.1
                if c == ')':
                    mult /= 1.1

            if mult != 1.0:
                self.token_mults[ident] = mult

        self.id_start = self.wrapped.tokenizer.bos_token_id
        self.id_end = self.wrapped.tokenizer.eos_token_id
        self.id_pad = self.id_end