def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--filter", "-k", action="append", help="filter benchmarks with regexp"
    )
    parser.add_argument(
        "--exclude", "-x", action="append", help="filter benchmarks with regexp"
    )
    parser.add_argument("--devices", "-d", action="append", help="cpu or cuda")
    parser.add_argument("--size", "-s", action="append", help="cpu or cuda")
    parser.add_argument(
        "--repeat", "-n", type=int, default=30, help="number of timing runs"
    )
    parser.add_argument(
        "--threads", "-t", type=int, help="number of threads to use for eager"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="enable verbose debug printouts"
    )
    parser.add_argument(
        "--nvfuser", action="store_true", help="enable nvfuser globally"
    )
    parser.add_argument("--transpose", action="store_true", help="transpose one input")
    parser.add_argument("--broadcast", action="store_true", help="broadcast one input")
    args = parser.parse_args()

    # defaults
    args.devices = args.devices or ["cpu", "cuda"]
    args.filter = args.filter or [r"."]
    args.exclude = args.exclude or [r"^$"]
    args.size = args.size or [64, 256, 1024, 4096, 8192]

    if args.nvfuser:
        torch._C._jit_override_can_fuse_on_cpu(False)
        torch._C._jit_override_can_fuse_on_gpu(False)
        torch._C._jit_set_texpr_fuser_enabled(False)
        torch._C._jit_set_nvfuser_enabled(True)
    else:
        torch._C._jit_override_can_fuse_on_cpu(torch._C._llvm_enabled())
        torch._C._jit_override_can_fuse_on_gpu(True)
        torch._C._jit_set_texpr_fuser_enabled(True)
        if torch.cuda.is_available():
            torch._C._jit_set_nvfuser_enabled(False)

    if args.threads:
        torch.set_num_threads(args.threads)
        torch._inductor.config.cpp.threads = args.threads

    if args.verbose:
        torch._inductor.config.debug = True

    torch._inductor.config.triton.autotune_pointwise = True

    rows = []
    for model in (MicroBenchmarks.sum, MicroBenchmarks.view):
        nargs = len(inspect.signature(model).parameters)
        for device in args.devices:
            for n in args.size:
                n = int(n)
                sys.stdout.write(f"{model.__name__:10} {device:4} {n:5} ")
                sys.stdout.flush()
                inputs = [torch.rand((n, n), device=device) for _ in range(nargs)]
                if args.broadcast:
                    inputs[-1] = torch.rand((1, n), device=device)
                if args.transpose:
                    inputs[-1] = inputs[-1].transpose(0, 1)
                result = microbenchmark(args, model, inputs)
                rows.append([model.__name__, device, str(n)] + result)
                print(" ".join(f"{v:.2f}x" for v in result))

    print(
        tabulate.tabulate(
            rows,
            headers=[
                "model",
                "dev",
                "n",
                "ts",
                "inductor",
            ],
        )
    )