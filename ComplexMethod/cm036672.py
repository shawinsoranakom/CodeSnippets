def test_rocm_wvsplitkrc_kernel(xnorm, n, k, m, dtype, seed, padded_a, bias_mode):
    torch.manual_seed(seed)
    cu_count = num_compute_units()

    # Next ^2 of n
    N_p2 = 1 << (n - 1).bit_length()
    # With 64 Ms per CU (each of 4 SIMDs working on a 16x16 tile),
    # and each working on a 512-shard of K, how many CUs would we need?
    rndup_cus = ((m + 64 - 1) // 64) * ((k + 512 - 1) // 512)
    # How many of 4 waves in a group can work on same 16 Ms at same time?
    # This reduces the Ms each group works on, i.e. increasing the number of CUs needed.
    GrpsShrB = min(N_p2 // 16, 4)
    # Given the above, how many CUs would we need?
    CuNeeded = rndup_cus * GrpsShrB
    # candidate for atomic reduce count splitk?
    fits_wvsplitkrc = (N_p2 * m * ((k + 512 - 1) // 512)) <= 128 * 1024 * 12
    fits_wvsplitkrc &= CuNeeded <= cu_count

    if not fits_wvsplitkrc:
        pytest.skip("Too large for wvSplitKrc")

    xavier = (
        math.sqrt(2 / k) if xnorm else 1
    )  # normalize to avoid large output-bias deltas
    A = (torch.rand(n, k, dtype=dtype, device="cuda") * 2 - 1) * xavier
    B = (torch.rand(m, k, dtype=dtype, device="cuda") * 2 - 1) * xavier
    if padded_a:
        A = pad_fp8(A)

    BIAS = None
    if bias_mode == 1:
        BIAS = torch.rand(m, dtype=dtype, device="cuda") * 2 - 1
    elif bias_mode == 2:
        BIAS = torch.rand(n, m, dtype=dtype, device="cuda") * 2 - 1
    elif bias_mode == 3:
        BIAS = torch.rand(1, m, dtype=dtype, device="cuda") * 2 - 1

    ref_out = torch.nn.functional.linear(A, B, BIAS)
    out = ops.wvSplitKrc(A, B, cu_count, BIAS)

    if xnorm:
        torch.testing.assert_close(out, ref_out, atol=1e-3, rtol=1e-8)
    else:
        torch.testing.assert_close(out, ref_out, atol=1e-3, rtol=1e-2)