def heal_tokens(
        self, input_ids: torch.LongTensor, tokenizer: Optional["PreTrainedTokenizerBase"] = None
    ) -> torch.LongTensor:
        r"""
        Generates sequences of token ids for models with a language modeling head.
        Parameters:
            input_ids (`torch.LongTensor`): The sequence used as a prompt for the generation.
            tokenizer (`PreTrainedTokenizerBase`, *optional*): The tokenizer used to decode the input ids.
        Return:
            `torch.LongTensor` where each sequence has its tail token replaced with its appropriate extension.
        """
        if tokenizer is None:
            raise ValueError(
                " When generating with token healing, you must pass the model's tokenizer to the `tokenizer` "
                "argument of `generate`."
            )

        bos_token_id, pad_token_id = tokenizer.bos_token_id, tokenizer.pad_token_id
        vocab_trie = ExtensionsTrie(tokenizer.get_vocab())
        generation_config = GenerationConfig(max_new_tokens=1, pad_token_id=pad_token_id)

        # assumption: leading/trailing whitespace is not meaningful, so the prompts are
        # stripped before re-tokenizing to desensitize generation to whitespace artefacts
        prompts = [p.strip() for p in tokenizer.decode(input_ids, skip_special_tokens=True)]
        input_ids = tokenizer(
            prompts,
            return_tensors="pt",
            padding=True,
        ).input_ids.to(input_ids.device)

        # replace bos with pad to not condition healing on it
        input_ids = torch.where(input_ids == bos_token_id, pad_token_id, input_ids)

        # the latter code assumes the input_ids is not empty, input_id has to be checked if contains elements
        if input_ids.numel() == 0:
            return input_ids

        tail_ids = input_ids[:, -1].tolist()

        # tail tokens are used for a prefix search, thus, whitespaces are replaced with
        # their tokenization (e.g. 'Ġ') to enable search for tokens prefixed with a whitespace
        if tokenizer.convert_tokens_to_ids(" ") is not None:
            space_tok = tokenizer.convert_ids_to_tokens(tokenizer.convert_tokens_to_ids(" "))[0]
            tail_toks = (cast(str, tokenizer.decode(t)).replace(" ", space_tok) for t in tail_ids)
        else:
            tail_toks = (cast(str, tokenizer.decode(t)) for t in tail_ids)

        for batch_idx, (tail_id, tail_tok) in enumerate(zip(tail_ids, tail_toks)):
            batch_ids = input_ids[batch_idx]
            if torch.all(batch_ids == pad_token_id).item():
                continue  # skip empty sequences (all pad ids)

            # apply bias for alternatives (extensions) to the tail token
            """
            seq_bias key has to be tuple with int so have to use
            tokenizer function to convert str to int
			"""
            seq_bias = {
                (tokenizer.convert_tokens_to_ids(alt_tok),): 10.0 for alt_tok in vocab_trie.extensions(prefix=tail_tok)
            }

            if len(seq_bias) == 1:
                continue  # skip if there are no token alternatives to heal with

            # slightly favor original token to limit aggressive healing e.g. 'http' -> 'https'
            seq_bias[(tail_id,)] += 1.0
            generation_config.update(sequence_bias=seq_bias)

            trimmed_ids = batch_ids[:-1]

            """
            the latter code assumes trimmed_ids is not empty
            so have to check the its element count
			"""
            if trimmed_ids.numel() == 0:
                continue

            # if the prompt is a single (non-pad) token, regenerate from bos
            if len(batch_ids[batch_ids != pad_token_id]) == 1:
                trimmed_ids[-1] = bos_token_id

            input_ids[batch_idx] = self.generate(trimmed_ids.unsqueeze(0), generation_config=generation_config)

        return input_ids