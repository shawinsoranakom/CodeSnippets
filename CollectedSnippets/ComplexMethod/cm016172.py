def run_benchmarks(benchmarks, sizes):
    df = pd.DataFrame(columns=["name", "N", "M", "nnc_time", "torch_time", "ratio"])
    with torch.no_grad():
        for name, nnc_fun, torch_fun, shape_fn in benchmarks:
            for N, M in sizes:
                iters = int(1e6 / (N + M))
                with kernel_arena_scope():
                    if shape_fn is None:
                        tA = torch.rand(M, N).clamp(0.01, 0.99)
                        tB = torch.rand(M, N).clamp(0.01, 0.99)
                        tX = torch.empty(M, N)
                        tR = torch.empty(M, N)
                    else:
                        tA, tB, tX = shape_fn(M, N)
                        tR = tX.clone()

                    def get_nnc_type(dtype):
                        if dtype == torch.float:
                            return torch._C._te.Dtype.Float
                        elif dtype == torch.long:
                            return torch._C._te.Dtype.Long

                    dtype = get_nnc_type(tA.dtype)

                    dM = torch._C._te.ExprHandle.int(M)
                    dN = torch._C._te.ExprHandle.int(N)

                    A = torch._C._te.Placeholder("A", dtype, [dM, dN])
                    B = torch._C._te.Placeholder("B", dtype, [dM, dN])

                    dim_args = [
                        torch._C._te.DimArg(*args) for args in [(dM, "m"), (dN, "n")]
                    ]

                    compute = nnc_fun(A, B)
                    X = torch._C._te.Compute("X", dim_args, compute)
                    loopnest = torch._C._te.LoopNest([X])
                    loopnest.prepare_for_codegen()
                    stmt = torch._C._te.simplify(loopnest.root_stmt())
                    cg = torch._C._te.construct_codegen(
                        "llvm", stmt, [torch._C._te.BufferArg(x) for x in [A, B, X]]
                    )

                    # warmup
                    for _ in range(10):
                        cg.call([tA, tB, tX])
                    start = time.time()
                    for it in range(iters):
                        cg.call([tA, tB, tX])
                    time1 = time.time() - start

                    fn = torch_fun(tA, tB, tR)
                    # warmup
                    for _ in range(10):
                        tR = fn()
                    start = time.time()
                    for it in range(iters):
                        tR = fn()
                    time2 = time.time() - start

                    df = df.append(
                        {
                            "name": name,
                            "N": N,
                            "M": M,
                            "nnc_time": time1,
                            "torch_time": time2,
                            "ratio": time2 / time1,
                        },
                        ignore_index=True,
                    )
                    print(name, N, M)

                    print(time2 / time1, time1, time2)
                    print()

                    def check_correctness(a, b):
                        if not np.allclose(a, b):
                            print(name)
                            raise AssertionError(f"Arrays not close for {name}")

                    check_correctness(tX, tR)
    return df