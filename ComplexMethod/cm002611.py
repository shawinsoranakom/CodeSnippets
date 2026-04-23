def extract_vocab_merges_from_model(self, tiktoken_url: str):
        import base64
        import json

        with open(self.vocab_file, "r", encoding="utf-8") as f:
            untyped = json.load(f)
        self.pattern = untyped["config"]["pattern"]
        self.additional_special_tokens = [
            AddedToken(k["token_str"], special=k["is_control"]) for k in untyped["special_tokens"]
        ]
        bpe_ranks = untyped["vocab"]
        byte_encoder = bytes_to_unicode()

        @lru_cache
        def token_bytes_to_string(b):
            return "".join([byte_encoder[ord(char)] for char in b.decode("latin-1")])

        merges = []
        vocab = {}
        for idx, token in enumerate(self.additional_special_tokens):
            vocab[token.content] = idx
        bpe_ranks = [base64.b64decode(k["token_bytes"]) for k in bpe_ranks]
        rank_set = set(bpe_ranks)
        token_to_rank = {token: rank for rank, token in enumerate(bpe_ranks)}
        for rank, token in enumerate(tqdm(bpe_ranks, desc="Converting tekken.json to tokenizer.json")):
            vocab[token_bytes_to_string(token)] = rank
            if len(token) == 1:
                continue
            local = []
            for index in range(1, len(token)):
                piece_l, piece_r = token[:index], token[index:]
                if piece_l in rank_set and piece_r in rank_set and (piece_l + piece_r) in rank_set:
                    local.append((piece_l, piece_r, rank))
            local = sorted(local, key=lambda x: (token_to_rank[x[0]], token_to_rank[x[1]]), reverse=False)
            merges.extend(local)
        merges = sorted(merges, key=lambda val: val[2], reverse=False)
        merges = [(token_bytes_to_string(val[0]), token_bytes_to_string(val[1])) for val in merges]
        return vocab, merges