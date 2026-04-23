def get_dataloader(
    tokenizer,
    sequence_length,
    dataset,
    num_samples=128,
    *,
    strategy="strided",
    seed=42,
    stride=None,
    eos_id=None,
):
    """
    Prepares and chunks the calibration dataloader, repeating short datasets.
    All processing happens on the CPU.

    Args:
        tokenizer: The tokenizer to use for text splitting.
        sequence_length: The length of each input sequence.
        dataset: The dataset to sample from.
        num_samples: The number of samples to generate.
        strategy: The sampling strategy to use. Possible values are
         1. "strided": Samples are taken at regular intervals.
         2. "linspace": Samples are taken at evenly spaced intervals.
         3. "random": Samples are taken at random positions.
        seed: The random seed for reproducibility. Used only if
         strategy="random"
        stride: The stride length for "strided" sampling.
        eos_id: The end-of-sequence token ID.

    Returns:
        np.ndarray of shape (num_samples, 1, sequence_length), dtype int32.
    """
    if not hasattr(dataset, "__iter__") or isinstance(dataset, (str, bytes)):
        raise TypeError(
            "The `dataset` argument must be an iterable (e.g., a list of "
            "strings, a generator, or a NumPy array). Got type: "
            f"{type(dataset).__name__}. Please pass the loaded dataset "
            "directly."
        )

    dataset_list = list(dataset)
    if not dataset_list:
        raise ValueError("Provided dataset is empty.")

    pieces = []
    if isinstance(dataset_list[0], str):
        for i, s in enumerate(dataset_list):
            toks = ops.convert_to_numpy(tokenizer.tokenize(s)).reshape(-1)
            pieces.append(toks)
            # avoid windows that span document boundaries
            if eos_id is not None and i < len(dataset_list) - 1:
                pieces.append(np.array([eos_id], dtype=np.int32))
    else:
        for s in dataset_list:
            toks = ops.convert_to_numpy(s).reshape(-1)
            pieces.append(toks.astype(np.int32, copy=False))

    all_tokens = (
        pieces[0].astype(np.int32, copy=False)
        if len(pieces) == 1
        else np.concatenate(pieces, axis=0).astype(np.int32, copy=False)
    )

    required_tokens = num_samples * sequence_length
    if all_tokens.size < required_tokens:
        repeats = math.ceil(required_tokens / max(1, all_tokens.size))
        all_tokens = np.tile(all_tokens, repeats)

    max_start = all_tokens.size - sequence_length
    if max_start < 0:
        raise ValueError(
            f"Not enough tokens to form one sample of length {sequence_length} "
            f"(have {all_tokens.size})."
        )

    # Choose deterministic, well-spread starts by default
    if strategy == "random":
        rng = np.random.default_rng(seed)
        starts = rng.integers(
            0, max_start + 1, size=num_samples, dtype=np.int64
        )
    elif strategy == "linspace":
        # even coverage with no RNG
        starts = np.linspace(0, max_start, num_samples, dtype=np.int64)
    elif strategy == "strided":
        # stride chosen to cover the space roughly uniformly
        if stride is None:
            stride = max(1, (max_start + 1) // num_samples)
        # offset derived deterministically from seed
        offset = (
            (abs(hash(("gptq-calib", seed))) % (max_start + 1))
            if max_start > 0
            else 0
        )
        starts = (offset + np.arange(num_samples, dtype=np.int64) * stride) % (
            max_start + 1
        )
    else:
        raise ValueError(f"Unknown strategy: {strategy}")

    # Gather contiguous windows
    # sliding_window_view avoids building a big index matrix
    windows = np.lib.stride_tricks.sliding_window_view(
        all_tokens, sequence_length
    )
    samples = windows[starts]  # (num_samples, sequence_length)
    return samples.astype(np.int32)[:, None, :]