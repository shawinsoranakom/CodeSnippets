def get_vocabulary(self, include_special_tokens=True):
        """Returns the current vocabulary of the layer.

        Args:
            include_special_tokens: If `True`, the returned vocabulary
                will include mask and OOV tokens,
                and a term's index in the vocabulary
                will equal the term's index when calling the layer.
                If `False`, the returned vocabulary will not include
                any mask or OOV tokens.
        """
        # The lookup table data will not be sorted, so we will create a inverted
        # lookup here, and use that to lookup a range of indices
        # [0, vocab_size).
        if self.lookup_table.size() == 0:
            vocab, indices = [], []
        else:
            keys, values = self.lookup_table.export()
            vocab, indices = (values, keys) if self.invert else (keys, values)
            vocab, indices = (
                self._tensor_vocab_to_numpy(vocab),
                indices.numpy(),
            )
        lookup = collections.defaultdict(
            lambda: self.oov_token, zip(indices, vocab)
        )
        vocab = [lookup[x] for x in range(self.vocabulary_size())]
        if self.mask_token is not None and self.output_mode == "int":
            vocab[0] = self.mask_token
        if not include_special_tokens:
            vocab = vocab[self._token_start_index() :]
        if self.vocabulary_dtype == "string":
            return [
                i.decode("utf-8") if isinstance(i, bytes) else i for i in vocab
            ]
        else:
            return vocab