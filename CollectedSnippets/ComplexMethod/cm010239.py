def main(op="scatter_mm", force=False, dtype=torch.float16, verbose=True):
    import itertools

    sizes_lst = [
        256,
        512,
        1024,
        2048,
        4096,
        8192,
        16384,
        32768,
        65536,
        131072,
        50432,
        65792,
    ]
    sizes3_lst = [3 * sz for sz in [64, 128] + sizes_lst if sz <= 2048]
    shapes_lst = [(sz, sz) for sz in sizes_lst[:-4] + sizes3_lst]
    shapes_lst.extend([(3072, 768), (768, 3072)])
    shapes_lst.extend([(5120, 1280), (1280, 5120)])
    if dtype is torch.int8:
        # triton does not support smaller blocks than 32
        blocksize_lst = [(32, 32), (64, 64), (128, 128), (256, 256)]
    else:
        blocksize_lst = [(16, 16), (32, 32), (64, 64), (128, 128)]
    sparsity_lst = [0.5, 0.7, 0.3][:1]
    for sparsity in sparsity_lst:
        print(f"{op, dtype, sparsity=}")
        try:
            for (M, K), N, (BM, BK) in itertools.product(
                shapes_lst, sizes_lst, blocksize_lst
            ):
                if not (BM <= M and BK <= K and M % BM == 0 and K % BK == 0):
                    continue
                if op == "scatter_mm":
                    optimize_scatter_mm(
                        M, K, N, BM, BK, force=force, sparsity=sparsity, dtype=dtype
                    )
                elif op in {"bsr_dense_addmm", "_int_bsr_dense_addmm"}:
                    if M == K and N == 50432:
                        continue
                    print(f"{M, K, N, (BM, BK)=}")
                    for alpha, beta in [(1, 1), (1, 0)]:
                        optimize_bsr_dense_addmm(
                            M,
                            K,
                            N,
                            BM,
                            BK,
                            beta=beta,
                            alpha=alpha,
                            force=force,
                            sparsity=sparsity,
                            dtype=dtype,
                            verbose=verbose,
                            opname=op,
                        )
                else:
                    raise NotImplementedError(op)
        except KeyboardInterrupt:
            break
        except Exception:
            dump()
            raise
    dump()

    if 0:
        # Check performance dependence on sparsity and apply
        # adjustments when differences are noticeable (more than 10%).
        #
        # When using NVIDIA A100 GPU, the performance dependence on
        # sparsity is insignificant (0 % ... 10 %) for majority of
        # shapes/blocksizes combinations. However, for a very few
        # specific size combinations, the effect of sparsity on
        # performance can be up to 20 %.
        for (M, K), N, (BM, BK) in itertools.product(
            shapes_lst, sizes_lst, blocksize_lst
        ):
            meta_lst: list = []
            key = (M, K, N, BM, BK)
            for sparsity1 in sparsity_lst:
                torch.manual_seed(0)
                bsr = create_blocked_tensor(
                    0, M, K, (BM, BK), sparsity1, dtype, device="cuda"
                ).to_sparse_bsr((BM, BK))
                dense = make_tensor(K, N, dtype=dtype, device="cuda")
                meta_lst = []
                for sparsity in sparsity_lst:
                    meta = get_meta(op, key, version=(0, dtype, sparsity), exact=True)
                    if meta is None:
                        continue

                    def bench(meta, bsr=bsr, dense=dense):
                        import triton

                        if op == "scatter_mm":
                            from torch.sparse._triton_ops import (
                                bsr_scatter_mm,
                                bsr_scatter_mm_indices_data,
                            )

                            indices_data = bsr_scatter_mm_indices_data(
                                bsr,
                                dense,
                                indices_format="bsr_strided_mm_compressed",
                                **meta,
                            )

                            def test_func():
                                return bsr_scatter_mm(
                                    bsr, dense, indices_data=indices_data
                                )

                        else:
                            raise NotImplementedError(op)

                        ms_min = triton.testing.do_bench(test_func, warmup=500, rep=100)

                        return ms_min

                    meta_lst.append(
                        (bench(meta), sparsity, tuple(meta[k] for k in sorted(meta)))
                    )
                if not meta_lst:
                    continue
                meta_lst = sorted(meta_lst)
                index = next(
                    i for i, item in enumerate(meta_lst) if item[1] == sparsity1
                )
                if meta_lst[0][2] == meta_lst[index][2]:
                    continue
                speeddiff = (1 - meta_lst[index][0] / meta_lst[0][0]) * 100
                if abs(speeddiff) < 10:
                    continue

                print(sparsity1, index, key, meta_lst, speeddiff)

                if index > 0:
                    device_name = _get_device_name()
                    meta = get_meta(
                        op, key, version=(0, dtype, meta_lst[0][1]), exact=True
                    )
                    update(
                        op,
                        device_name,
                        (0, dtype, sparsity1),
                        key,
                        tuple(meta[k] for k in sorted(meta)),
                    )
                    print("update")
                    dump()