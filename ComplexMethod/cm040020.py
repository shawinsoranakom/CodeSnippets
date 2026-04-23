def adapt(self, data, batch_size=None, steps=None):
        """Computes a vocabulary of string terms from tokens in a dataset.

        Calling `adapt()` on a `TextVectorization` layer is an alternative to
        passing in a precomputed vocabulary on construction via the `vocabulary`
        argument. A `TextVectorization` layer should always be either adapted
        over a dataset or supplied with a vocabulary.

        During `adapt()`, the layer will build a vocabulary of all string tokens
        seen in the dataset, sorted by occurrence count, with ties broken by
        sort order of the tokens (high to low). At the end of `adapt()`, if
        `max_tokens` is set, the vocabulary will be truncated to `max_tokens`
        size. For example, adapting a layer with `max_tokens=1000` will compute
        the 1000 most frequent tokens occurring in the input dataset. If
        `output_mode='tf-idf'`, `adapt()` will also learn the document
        frequencies of each token in the input dataset.

        Arguments:
            data: The data to train on. It can be passed either as a
                batched `tf.data.Dataset`, as a list of strings,
                as a NumPy array, or as any iterable of batches (e.g.
                a generator yielding batches of strings).
            steps: Integer or `None`.
                Total number of steps (batches of samples) to process.
                If `data` is a `tf.data.Dataset`, and `steps` is `None`,
                `adapt()` will run until the input dataset is exhausted.
                When passing an infinitely
                repeating dataset, you must specify the `steps` argument. This
                argument is not supported with array inputs or list inputs.
        """
        self.reset_state()
        if isinstance(data, tf.data.Dataset):
            if steps is not None:
                data = data.take(steps)
            for batch in data:
                self.update_state(batch)
        elif hasattr(data, "__iter__") and not (
            isinstance(data, (list, tuple, np.ndarray))
            or backend.is_tensor(data)
            or tf.is_tensor(data)
        ):
            for i, batch in enumerate(data):
                if steps is not None and i >= steps:
                    break
                self.update_state(batch)
        else:
            data = tf_utils.ensure_tensor(data, dtype="string")
            if data.shape.rank == 1:
                data = tf.expand_dims(data, -1)
            self.update_state(data)
        self.finalize_state()