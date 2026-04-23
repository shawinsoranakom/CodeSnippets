def run_segment_reduce_test(
        self,
        segment_reduce_op,
        element_wise_reduce_method,
        num_indices,
        indices_high,
        data_dims=tuple(),
        num_segments=None,
        add_neg1_to_indices=False,
        sorted_indices=False,
    ):
        if num_segments is not None and indices_high >= num_segments:
            raise ValueError("Indices high cannot be more than num segments")
        indices_dims = (num_indices,)
        full_data_dims = indices_dims + data_dims
        data = np.random.rand(*full_data_dims).astype(np.float32)
        segment_ids = np.concatenate(
            [
                np.arange(indices_high),
                np.random.randint(
                    low=0,
                    high=indices_high,
                    size=(indices_dims[0] - indices_high),
                ),
            ]
        ).astype(np.int32)
        if sorted_indices:
            segment_ids = np.sort(segment_ids, axis=-1)
        if add_neg1_to_indices:
            segment_ids[0] = -1
        outputs = segment_reduce_op(
            data, segment_ids, num_segments, sorted=sorted_indices
        )
        if num_segments is None:
            num_segments = np.max(segment_ids).item() + 1
        expected_shape = (num_segments,) + data_dims
        if segment_reduce_op == kmath.segment_max:
            if backend.backend() == "tensorflow":
                empty_fill_value = -np.finfo(np.float32).max
            else:
                empty_fill_value = -np.inf
            expected = np.full(expected_shape, empty_fill_value)
        else:
            expected = np.zeros(expected_shape)

        for idx in range(num_indices):
            segment_id = segment_ids[idx]
            if segment_id == -1:
                continue
            expected[segment_id] = element_wise_reduce_method(
                expected[segment_id], data[idx]
            )
        self.assertAllClose(outputs, expected)