def run_test_targets(self, model, tokenizer):
        vocab = tokenizer.get_vocab()
        targets = sorted(vocab.keys())[:2]
        # Pipeline argument
        fill_masker = FillMaskPipeline(model=model, tokenizer=tokenizer, targets=targets)
        outputs = fill_masker(f"This is a {tokenizer.mask_token}")
        self.assertEqual(
            outputs,
            [
                {"sequence": ANY(str), "score": ANY(float), "token": ANY(int), "token_str": ANY(str)},
                {"sequence": ANY(str), "score": ANY(float), "token": ANY(int), "token_str": ANY(str)},
            ],
        )
        target_ids = {vocab[el] for el in targets}
        self.assertEqual({el["token"] for el in outputs}, target_ids)
        processed_targets = [tokenizer.decode([x]) for x in target_ids]
        self.assertEqual({el["token_str"] for el in outputs}, set(processed_targets))

        # Call argument
        fill_masker = FillMaskPipeline(model=model, tokenizer=tokenizer)
        outputs = fill_masker(f"This is a {tokenizer.mask_token}", targets=targets)
        self.assertEqual(
            outputs,
            [
                {"sequence": ANY(str), "score": ANY(float), "token": ANY(int), "token_str": ANY(str)},
                {"sequence": ANY(str), "score": ANY(float), "token": ANY(int), "token_str": ANY(str)},
            ],
        )
        target_ids = {vocab[el] for el in targets}
        self.assertEqual({el["token"] for el in outputs}, target_ids)
        processed_targets = [tokenizer.decode([x]) for x in target_ids]
        self.assertEqual({el["token_str"] for el in outputs}, set(processed_targets))

        # Score equivalence
        outputs = fill_masker(f"This is a {tokenizer.mask_token}", targets=targets)
        tokens = [top_mask["token_str"] for top_mask in outputs]
        scores = [top_mask["score"] for top_mask in outputs]

        # For some BPE tokenizers, `</w>` is removed during decoding, so `token_str` won't be the same as in `targets`.
        if set(tokens) == set(targets):
            unmasked_targets = fill_masker(f"This is a {tokenizer.mask_token}", targets=tokens)
            target_scores = [top_mask["score"] for top_mask in unmasked_targets]
            self.assertEqual(nested_simplify(scores), nested_simplify(target_scores))

        # Raises with invalid
        with self.assertRaises(ValueError):
            outputs = fill_masker(f"This is a {tokenizer.mask_token}", targets=[])
        # For some tokenizers, `""` is actually in the vocabulary and the expected error won't raised
        if "" not in tokenizer.get_vocab():
            with self.assertRaises(ValueError):
                outputs = fill_masker(f"This is a {tokenizer.mask_token}", targets=[""])
            with self.assertRaises(ValueError):
                outputs = fill_masker(f"This is a {tokenizer.mask_token}", targets="")