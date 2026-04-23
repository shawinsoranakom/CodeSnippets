def update_state(self, data):
        if self._has_input_vocabulary:
            raise ValueError(
                f"Cannot adapt layer '{self.name}' after setting a static "
                "vocabulary via `vocabulary` argument or "
                "`set_vocabulary()` method."
            )

        data = tf_utils.ensure_tensor(data, dtype=self.vocabulary_dtype)
        if data.shape.rank == 0:
            data = tf.expand_dims(data, 0)
        if data.shape.rank == 1:
            # Expand dims on axis 0 for tf-idf. A 1-d tensor
            # is a single document.
            data = tf.expand_dims(data, 0)

        tokens, counts = self._num_tokens(data)
        self.token_counts.insert(
            tokens, counts + self.token_counts.lookup(tokens)
        )

        if self.output_mode == "tf_idf":
            # Dedupe each row of our dataset.
            if isinstance(data, tf.RaggedTensor):
                deduped_doc_data = tf.map_fn(lambda x: tf.unique(x)[0], data)
            else:
                deduped_doc_data = [tf.unique(x)[0] for x in data]
                deduped_doc_data = tf.concat(deduped_doc_data, axis=0)
            # Flatten and count tokens.
            tokens, counts = self._num_tokens(deduped_doc_data)

            self.token_document_counts.insert(
                tokens, counts + self.token_document_counts.lookup(tokens)
            )
            if isinstance(data, tf.RaggedTensor):
                self.num_documents.assign_add(data.nrows())
            else:
                self.num_documents.assign_add(
                    tf.shape(data, out_type="int64")[0]
                )