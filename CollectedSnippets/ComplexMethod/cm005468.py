def __init__(self, dict_):
        for k, v in dict_.items():
            setattr(self, k, v)

        if not hasattr(self, "merges"):
            if not hasattr(self, "tokens") or not hasattr(self, "scores"):
                raise ValueError(
                    "tokens and scores need to be passed for a LLaMa tokenizer without merges to be instantiated."
                )
            tokens = self.tokens
            scores = self.scores
            vocab = {t: scores[i] for i, t in enumerate(tokens)}

            logger.warning("Merges were not in checkpoint, building merges on the fly.")
            merges = []
            for merge, piece_score in tqdm(vocab.items()):
                local = []
                for index in range(1, len(merge)):
                    piece_l, piece_r = merge[:index], merge[index:]
                    if piece_l in tokens and piece_r in tokens:
                        local.append((piece_l, piece_r, piece_score))
                local = sorted(local, key=lambda x: (vocab[x[0]], vocab[x[1]]), reverse=True)
                merges.extend(local)
            merges = sorted(merges, key=lambda val: val[2], reverse=True)
            merges = [(val[0], val[1]) for val in merges]
            self.merges = merges
        else:
            self.merges = [tuple(merge.split(" ")) for merge in self.merges]
            if not hasattr(self, "scores"):
                self.scores = [None for _ in range(len(self.tokens))]

        if not hasattr(self, "added_tokens"):
            self.added_tokens = []

        if not hasattr(self, "unk_token_id"):
            self.unk_token_id = None

        # Llama2 uses the field `unknown_token_id`
        if hasattr(self, "unknown_token_id") and self.unk_token_id is None:
            self.unk_token_id = self.unknown_token_id