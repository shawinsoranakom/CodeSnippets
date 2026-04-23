def bsr_dense_addmm_meta(
    M,
    K,
    N,
    Ms,
    Ks,
    beta,
    alpha,
    SPLIT_N=None,
    GROUP_SIZE_ROW=None,
    num_warps=None,
    num_stages=None,
    sparsity=None,
    dtype=None,
    out_dtype=None,
    _version=0,
    **extra,
):
    # Specifying _version is useful for situations when one wants to
    # discard existing triton kernel tuning results, say, in testing
    # bsr_dense_addmm_meta functionality.
    if dtype is None:
        dtype = torch.float16
    if out_dtype is None:
        out_dtype = dtype
    if sparsity is None:
        sparsity = 0.5
    if {SPLIT_N, num_warps, num_stages, GROUP_SIZE_ROW} == {None}:
        device_name = _get_device_name()
        key = (M, K, N, Ms, Ks, beta == 0, beta == 1, alpha == 1)
        if dtype is out_dtype:
            version_dtype = dtype
        else:
            version_dtype = dtype, out_dtype
        meta = get_meta(
            "bsr_dense_addmm",
            key,
            device_name,
            version=(_version, version_dtype, sparsity),
        )
        if meta is None and sparsity != 0.5:
            meta = get_meta(
                "bsr_dense_addmm",
                key,
                device_name,
                version=(_version, version_dtype, 0.5),
            )
        if meta is None and dtype is not out_dtype:
            meta = get_meta(
                "bsr_dense_addmm", key, device_name, version=(_version, dtype, 0.5)
            )
        if meta is None:
            # find approximate meta such that N % SPLIT_N == 0.
            matching_meta = get_meta(
                "bsr_dense_addmm",
                (*key[:2], "*", *key[3:]),
                device_name,
                version=(_version, version_dtype, 0.5),
            )
            if matching_meta is None and dtype is not out_dtype:
                matching_meta = get_meta(
                    "bsr_dense_addmm",
                    (*key[:2], "*", *key[3:]),
                    device_name,
                    version=(_version, dtype, 0.5),
                )
            for mkey in sorted(matching_meta or {}):
                meta_ = matching_meta[mkey]
                n = mkey[2]
                split_n = meta_["SPLIT_N"]
                c = n // split_n
                if N % c == 0 and n <= N:
                    meta = dict(meta_)
                    meta["SPLIT_N"] = N // c
        if meta is not None:
            meta.update(**extra)
            return meta
        else:
            # see [Computing optimal kernel parameters] in
            # _triton_ops_meta.py for ways to avoid this warning
            # message
            warn_once(
                "bsr_dense_addmm uses non-optimal triton kernel parameters"
                f" for {M=} {K=} {N=} {Ms=}, {Ks=} {beta=} {alpha=} {dtype=} {out_dtype=}"
            )

    SPLIT_N = SPLIT_N or max(N // Ms, 1)
    GROUP_SIZE_ROW = GROUP_SIZE_ROW or 4
    num_stages = num_stages or 1
    num_warps = num_warps or 4
    return dict(
        SPLIT_N=SPLIT_N,
        GROUP_SIZE_ROW=GROUP_SIZE_ROW,
        num_stages=num_stages,
        num_warps=num_warps,
        **extra,
    )