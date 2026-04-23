def adapt(self, data, steps=None):
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
            data = tf_utils.ensure_tensor(data, dtype=self.vocabulary_dtype)
            if data.shape.rank == 1:
                data = tf.expand_dims(data, -1)
            self.update_state(data)
        self.finalize_state()