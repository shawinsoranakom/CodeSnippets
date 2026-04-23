def _timeseries_dataset_grain(
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

    # Compute number of sequences and start positions
    num_seqs = end_index - start_index - (sequence_length - 1) * sampling_rate
    if targets is not None:
        num_seqs = min(num_seqs, len(targets))

    start_positions = np.arange(0, num_seqs, sequence_stride)
    if shuffle:
        if seed is None:
            seed = np.random.randint(1e6)
        rng = np.random.RandomState(seed)
        rng.shuffle(start_positions)

    data_slice = np.array(data[start_index:end_index])

    # Build the list of sequences as numpy arrays
    sequences = []
    for pos in start_positions:
        indices = np.arange(
            pos, pos + sequence_length * sampling_rate, sampling_rate
        )
        sequences.append(data_slice[indices])

    seq_ds = grain.MapDataset.source(sequences)

    if targets is not None:
        target_slice = np.array(targets[start_index:])
        target_values = [target_slice[pos] for pos in start_positions]
        target_ds = grain.MapDataset.source(target_values)
        ds = grain.experimental.ZipMapDataset([seq_ds, target_ds])
    else:
        ds = seq_ds

    if shuffle:
        ds = ds.shuffle(seed=seed)

    ds = ds.to_iter_dataset()
    if batch_size is not None:
        ds = ds.batch(batch_size, batch_fn=make_batch)

    return ds