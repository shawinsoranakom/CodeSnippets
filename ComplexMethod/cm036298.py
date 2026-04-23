def test_is_uniform_decode() -> None:
    # Normal
    assert GPUModelRunner._is_uniform_decode(
        max_num_scheduled_tokens=1,
        uniform_decode_query_len=1,
        num_tokens=16,
        num_reqs=16,
    )
    assert not GPUModelRunner._is_uniform_decode(
        max_num_scheduled_tokens=2,
        uniform_decode_query_len=1,
        num_tokens=16,
        num_reqs=16,
    )
    assert not GPUModelRunner._is_uniform_decode(
        max_num_scheduled_tokens=1,
        uniform_decode_query_len=1,
        num_tokens=16,
        num_reqs=15,
    )
    # Spec decoding
    assert GPUModelRunner._is_uniform_decode(
        max_num_scheduled_tokens=5,
        uniform_decode_query_len=5,
        num_tokens=30,
        num_reqs=6,
    )
    assert not GPUModelRunner._is_uniform_decode(
        max_num_scheduled_tokens=5,
        uniform_decode_query_len=4,
        num_tokens=30,
        num_reqs=6,
    )
    assert not GPUModelRunner._is_uniform_decode(
        max_num_scheduled_tokens=5,
        uniform_decode_query_len=5,
        num_tokens=30,
        num_reqs=7,
    )
    # Force uniform decode
    assert GPUModelRunner._is_uniform_decode(
        max_num_scheduled_tokens=1,
        uniform_decode_query_len=1,
        num_tokens=16,
        num_reqs=16,
        force_uniform_decode=True,
    )
    assert GPUModelRunner._is_uniform_decode(
        max_num_scheduled_tokens=2,
        uniform_decode_query_len=1,
        num_tokens=16,
        num_reqs=16,
        force_uniform_decode=True,
    )
    assert GPUModelRunner._is_uniform_decode(
        max_num_scheduled_tokens=1,
        uniform_decode_query_len=1,
        num_tokens=16,
        num_reqs=15,
        force_uniform_decode=True,
    )
    assert not GPUModelRunner._is_uniform_decode(
        max_num_scheduled_tokens=1,
        uniform_decode_query_len=1,
        num_tokens=16,
        num_reqs=16,
        force_uniform_decode=False,
    )
    assert not GPUModelRunner._is_uniform_decode(
        max_num_scheduled_tokens=2,
        uniform_decode_query_len=1,
        num_tokens=16,
        num_reqs=16,
        force_uniform_decode=False,
    )
    assert not GPUModelRunner._is_uniform_decode(
        max_num_scheduled_tokens=1,
        uniform_decode_query_len=1,
        num_tokens=16,
        num_reqs=15,
        force_uniform_decode=False,
    )