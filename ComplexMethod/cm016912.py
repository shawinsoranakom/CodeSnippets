def compute_blake3_hash(
    fp: str | IO[bytes],
    chunk_size: int = DEFAULT_CHUNK,
    interrupt_check: InterruptCheck | None = None,
    checkpoint: HashCheckpoint | None = None,
) -> tuple[str | None, HashCheckpoint | None]:
    """Compute BLAKE3 hash of a file, with optional checkpoint support.

    Args:
        fp: File path or file-like object
        chunk_size: Size of chunks to read at a time
        interrupt_check: Optional callable that returns True if the operation
            should be interrupted (e.g. paused or cancelled). Must be
            non-blocking so file handles are released immediately. Checked
            between chunk reads.
        checkpoint: Optional checkpoint to resume from (file paths only)

    Returns:
        Tuple of (hex_digest, None) on completion, or
        (None, checkpoint) on interruption (file paths only), or
        (None, None) on interruption of a file object
    """
    if chunk_size <= 0:
        chunk_size = DEFAULT_CHUNK

    with _open_for_hashing(fp) as (f, is_path):
        if checkpoint is not None and is_path:
            f.seek(checkpoint.bytes_processed)
            h = checkpoint.hasher
            bytes_processed = checkpoint.bytes_processed
        else:
            h = blake3()
            bytes_processed = 0

        while True:
            if interrupt_check is not None and interrupt_check():
                if is_path:
                    return None, HashCheckpoint(
                        bytes_processed=bytes_processed,
                        hasher=h,
                    )
                return None, None
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
            bytes_processed += len(chunk)

        return h.hexdigest(), None