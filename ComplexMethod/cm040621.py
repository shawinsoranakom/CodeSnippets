def _timeseries_dataset_tf(
    data,
    targets,
    sequence_length,
    sequence_stride,
    sampling_rate,
    batch_size,
    shuffle,
    seed,
    start_index,
    end_index,
):
    if start_index is None:
        start_index = 0
    if end_index is None:
        end_index = len(data)

    # Determine the lowest dtype to store start positions (to lower memory
    # usage).
    num_seqs = end_index - start_index - (sequence_length - 1) * sampling_rate
    if targets is not None:
        num_seqs = min(num_seqs, len(targets))
    if num_seqs < 2147483647:
        index_dtype = "int32"
    else:
        index_dtype = "int64"

    # Generate start positions
    start_positions = np.arange(0, num_seqs, sequence_stride, dtype=index_dtype)
    if shuffle:
        if seed is None:
            seed = np.random.randint(1e6)
        rng = np.random.RandomState(seed)
        rng.shuffle(start_positions)

    sequence_length = tf.cast(sequence_length, dtype=index_dtype)
    sampling_rate = tf.cast(sampling_rate, dtype=index_dtype)

    positions_ds = tf.data.Dataset.from_tensors(start_positions).repeat()

    # For each initial window position, generates indices of the window elements
    indices = tf.data.Dataset.zip(
        (tf.data.Dataset.range(len(start_positions)), positions_ds)
    ).map(
        lambda i, positions: tf.range(
            positions[i],
            positions[i] + sequence_length * sampling_rate,
            sampling_rate,
        ),
        num_parallel_calls=tf.data.AUTOTUNE,
    )

    dataset = sequences_from_indices(data, indices, start_index, end_index)
    if targets is not None:
        indices = tf.data.Dataset.zip(
            (tf.data.Dataset.range(len(start_positions)), positions_ds)
        ).map(
            lambda i, positions: positions[i],
            num_parallel_calls=tf.data.AUTOTUNE,
        )
        target_ds = sequences_from_indices(
            targets, indices, start_index, end_index
        )
        dataset = tf.data.Dataset.zip((dataset, target_ds))
    dataset = dataset.prefetch(tf.data.AUTOTUNE)
    if batch_size is not None:
        if shuffle:
            # Shuffle locally at each iteration
            dataset = dataset.shuffle(buffer_size=batch_size * 8, seed=seed)
        dataset = dataset.batch(batch_size)
    else:
        if shuffle:
            dataset = dataset.shuffle(buffer_size=1024, seed=seed)
    return dataset