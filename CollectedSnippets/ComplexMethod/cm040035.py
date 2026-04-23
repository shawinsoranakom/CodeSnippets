def finalize_state(self):
        if self._has_input_vocabulary or tf.equal(self.token_counts.size(), 0):
            # Finalize idf_weights to a const for call even if we don't need to
            # compute a new vocabulary.
            if self.output_mode == "tf_idf":
                self.idf_weights_const = self.idf_weights.value()
            self._record_vocabulary_size()
            return

        # Remove special tokens from our counts.
        if self.mask_token is not None:
            self.token_counts.remove(
                tf.convert_to_tensor([self.mask_token], self.vocabulary_dtype)
            )
        if self.oov_token is not None:
            self.token_counts.remove(
                tf.convert_to_tensor([self.oov_token], self.vocabulary_dtype)
            )

        tokens, counts = self.token_counts.export()
        # To keep vocabs deterministic, we sort our tokens by count and break
        # ties by sorting the tokens themselves. Tensorflow has no ops for
        # sorting strings, so we need to use numpy for the sort.
        sorted_indices = np.lexsort((tokens.numpy(), counts.numpy()))[::-1]
        token_start = self._token_start_index()
        if self.max_tokens:
            max_learned_tokens = self.max_tokens - token_start
            sorted_indices = sorted_indices[:max_learned_tokens]
        tokens = tf.gather(tokens, sorted_indices)
        self.lookup_table = self._lookup_table_from_tokens(tokens)

        if self.output_mode == "tf_idf":
            token_document_counts = self.token_document_counts.lookup(tokens)
            idf_weights = self._inverse_document_frequency(
                token_document_counts, self.num_documents
            )
            idf_weights = tf.cast(idf_weights, backend.floatx())
            # Pad the front of idf_weights with the average idf weight for OOV
            # tokens.  We cannot compute the real idf weight of OOV in a single
            # pass.
            idf_weights = tf.pad(
                idf_weights,
                [[self._token_start_index(), 0]],
                constant_values=tf.reduce_mean(idf_weights),
            )
            if self.pad_to_max_tokens and self.max_tokens is not None:
                # Pad the back of idf_weights with zeros.
                idf_weights = tf.pad(
                    idf_weights,
                    [[0, self.max_tokens - tf.size(idf_weights)]],
                    constant_values=0,
                )
            self.idf_weights = tf.Variable(
                idf_weights,
                dtype=backend.floatx(),
                trainable=False,
            )
            self.idf_weights_const = self.idf_weights.value()

        # We call this here to save memory, now that we've built our vocabulary,
        # we don't want to keep every token we've seen in separate lookup
        # tables.
        self.reset_state()
        self._record_vocabulary_size()