def extract_vocab_merges_from_model(self, tiktoken_url: str):
        try:
            from tiktoken.load import load_tiktoken_bpe
        except Exception:
            raise ValueError(
                "`tiktoken` is required to read a `tiktoken` file. Install it with `pip install tiktoken`."
            )

        bpe_ranks = load_tiktoken_bpe(tiktoken_url)
        byte_encoder = bytes_to_unicode()

        def token_bytes_to_string(b):
            return "".join([byte_encoder[ord(char)] for char in b.decode("latin-1")])

        merges = []
        vocab = {}
        for token, rank in bpe_ranks.items():
            vocab[token_bytes_to_string(token)] = rank
            if len(token) == 1:
                continue
            local = []
            for index in range(1, len(token)):
                piece_l, piece_r = token[:index], token[index:]
                if piece_l in bpe_ranks and piece_r in bpe_ranks and (piece_l + piece_r) in bpe_ranks:
                    local.append((piece_l, piece_r, rank))
            local = sorted(local, key=lambda x: (bpe_ranks[x[0]], bpe_ranks[x[1]]), reverse=False)
            merges.extend(local)
        merges = sorted(merges, key=lambda val: val[2], reverse=False)
        merges = [(token_bytes_to_string(val[0]), token_bytes_to_string(val[1])) for val in merges]
        return vocab, merges