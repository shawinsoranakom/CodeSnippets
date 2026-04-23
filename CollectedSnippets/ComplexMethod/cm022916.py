def test_audio_buffer() -> None:
    """Test audio buffer wrapping."""

    samples_per_chunk = 160  # 10 ms
    bytes_per_chunk = samples_per_chunk * 2
    leftover_buffer = AudioBuffer(bytes_per_chunk)

    # Partially fill audio buffer
    half_chunk = bytes(it.islice(it.cycle(range(256)), bytes_per_chunk // 2))
    chunks = list(chunk_samples(half_chunk, bytes_per_chunk, leftover_buffer))

    assert not chunks
    assert leftover_buffer.bytes() == half_chunk

    # Fill and wrap with 1/4 chunk left over
    three_quarters_chunk = bytes(
        it.islice(it.cycle(range(256)), int(0.75 * bytes_per_chunk))
    )
    chunks = list(chunk_samples(three_quarters_chunk, bytes_per_chunk, leftover_buffer))

    assert len(chunks) == 1
    assert (
        leftover_buffer.bytes()
        == three_quarters_chunk[len(three_quarters_chunk) - (bytes_per_chunk // 4) :]
    )
    assert chunks[0] == half_chunk + three_quarters_chunk[: bytes_per_chunk // 2]

    # Run 2 chunks through
    leftover_buffer.clear()
    assert len(leftover_buffer) == 0

    two_chunks = bytes(it.islice(it.cycle(range(256)), bytes_per_chunk * 2))
    chunks = list(chunk_samples(two_chunks, bytes_per_chunk, leftover_buffer))

    assert len(chunks) == 2
    assert len(leftover_buffer) == 0
    assert chunks[0] == two_chunks[:bytes_per_chunk]
    assert chunks[1] == two_chunks[bytes_per_chunk:]