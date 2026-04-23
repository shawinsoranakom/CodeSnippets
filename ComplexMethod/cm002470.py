def as_tensor(value, dtype=None):
                if (
                    isinstance(value, (list, tuple))
                    and len(value) > 0
                    and isinstance(value[0], (list, tuple, np.ndarray))
                ):
                    value_lens = [len(val) for val in value]
                    if len(set(value_lens)) > 1 and dtype is None:
                        # we have a ragged list so handle explicitly
                        value = as_tensor([np.asarray(val) for val in value], dtype=object)
                if len(flatten(value)) == 0 and dtype is None:
                    dtype = np.int64
                return np.asarray(value, dtype=dtype)