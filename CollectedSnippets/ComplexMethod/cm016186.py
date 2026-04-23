def run(
    a: int,
    b: int,
    iters: int,
    batch_size: int,
    sequence_length: int,
    embed_dim: int,
    num_heads: int,
    device: str,
    dtype: str,
    block_size: int,
    seed,
):
    random.seed(seed)
    torch.manual_seed(seed)
    np.random.seed(seed)

    from scipy.stats import beta

    lengths = (
        beta.rvs(a, b, size=batch_size)
        * (sequence_length + block_size - 1)
        // block_size
    )
    lengths = list(map(int, list(lengths)))
    lengths = [l * block_size for l in lengths]
    lengths = [max(l, block_size) for l in lengths]

    # Used to enforce no padding
    # lengths = [sequence_length] * batch_size

    # Ensure one row in the batch of ele has the max_sequence_length
    lengths[random.randint(0, batch_size - 1)] = sequence_length

    q = [torch.randn(l, embed_dim, device=device, dtype=dtype) for l in lengths]
    q = torch.nested.nested_tensor(q, device=device, dtype=dtype)
    k, v = q, q

    qkv = torch.nn.Linear(embed_dim, 3 * embed_dim, device=device, dtype=dtype)
    proj = torch.nn.Linear(embed_dim, embed_dim, device=device, dtype=dtype)

    native_mha = torch.nn.MultiheadAttention(
        embed_dim, num_heads, batch_first=True, device=device, dtype=dtype
    ).eval()
    native_mha.in_proj_weight = qkv.weight
    native_mha.in_proj_bias = qkv.bias
    native_mha.out_proj.weight = proj.weight
    native_mha.out_proj.bias = proj.bias

    # Create query mask
    q_mask = torch.nested.to_padded_tensor(
        torch.nested.nested_tensor(
            [torch.tensor([True] * length, dtype=torch.bool) for length in lengths]
        ),
        0,
    )
    q_mask = q_mask.cuda()

    if q_mask.size(1) == 0:
        return None

    # Benchmark the native MHA in core
    with torch.backends.cuda.sdp_kernel(enable_math=False, enable_flash=True):
        with torch.inference_mode():
            time_native_mha_fast, y_native_mha_fast, _ = benchmark_torch_function(
                iters, native_mha, q, k, v, need_weights=False
            )
    q = q.to_padded_tensor(0)
    k = q
    v = q
    # Internal Flash Attention
    time_native_mha_slow, y_native_mha_slow, _ = benchmark_torch_function(
        iters, native_mha, q, k, v, key_padding_mask=~q_mask, need_weights=False
    )

    # Convert to padded for comparison
    if y_native_mha_fast.is_nested:
        y_native_mha_fast = torch.nested.to_padded_tensor(y_native_mha_fast, 0)
    y_native_mha_fast = y_native_mha_fast * q_mask.unsqueeze(-1)

    if y_native_mha_slow.is_nested:
        y_native_mha_slow = torch.nested.to_padded_tensor(y_native_mha_slow, 0)
    y_native_mha_slow = y_native_mha_slow * q_mask.unsqueeze(-1)

    # Correctness check
    entry_name = f"batch:{batch_size}_seq_len:{sequence_length}_n_heads:{num_heads}_embed_dim:{embed_dim}"
    try:
        torch.testing.assert_close(
            y_native_mha_fast, y_native_mha_slow, atol=1e-3, rtol=1e-3
        )
    except AssertionError:
        error_dict[entry_name] += 1
        pprint(error_dict)

    # Calculate amount of padding
    padding = 1 - q_mask.float().mean().item()

    # Calculate the speedup for flash attention
    speedup_fast_internal = time_native_mha_slow / time_native_mha_fast

    result_entry = OrderedDict()
    result_entry["dtype"] = dtype
    result_entry["batch_size"] = batch_size
    result_entry["sequence_length"] = sequence_length
    result_entry["n_heads"] = num_heads
    result_entry["embed_dim"] = embed_dim
    result_entry["time_native_mha_slow(\u00b5s)"] = f"{time_native_mha_slow:.3f}"
    result_entry["time_native_mha_fast (\u00b5s)"] = f"{time_native_mha_fast:.3f}"
    result_entry["speedup flash_mha v native_mha"] = f"{speedup_fast_internal:.3f}"
    result_entry["padding"] = f"{padding:.3f}"
    return result_entry