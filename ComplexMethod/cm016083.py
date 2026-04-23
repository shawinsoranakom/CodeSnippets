def main():
    parser = argparse.ArgumentParser(description="PyTorch distributed benchmark suite")
    parser.add_argument("--rank", type=int, default=os.environ["RANK"])
    parser.add_argument("--world-size", type=int, required=True)
    parser.add_argument("--distributed-backend", type=str, default="nccl")
    parser.add_argument("--bucket-size", type=int, default=25)
    parser.add_argument("--master-addr", type=str, required=True)
    parser.add_argument("--master-port", type=str, required=True)
    parser.add_argument("--model", type=str)
    parser.add_argument(
        "--json", type=str, metavar="PATH", help="Write file with benchmark results"
    )
    args = parser.parse_args()

    num_gpus_per_node = torch.cuda.device_count()
    if num_gpus_per_node != 8:
        raise AssertionError(
            f"Expected 8 GPUs per machine, but found {num_gpus_per_node}"
        )

    # The global process group used only for communicating benchmark
    # metadata, like measurements. Not for benchmarking itself.
    dist.init_process_group(
        backend="gloo",
        init_method=f"tcp://{args.master_addr}:{args.master_port}",
        rank=args.rank,
        world_size=args.world_size,
    )

    output = allgather_run("nvidia-smi topo -m")
    if not allequal(output):
        print('Output of "nvidia-smi topo -m" differs between machines')
        sys.exit(1)

    if args.rank == 0:
        print("-----------------------------------")
        print("PyTorch distributed benchmark suite")
        print("-----------------------------------")
        print()
        print(f"* PyTorch version: {torch.__version__}")
        print(f"* CUDA version: {torch.version.cuda}")
        print(f"* Distributed backend: {args.distributed_backend}")
        print(f"* Maximum bucket size: {args.bucket_size}MB")
        print()
        print("--- nvidia-smi topo -m ---")
        print()
        print(output[0])
        print("--------------------------")
        print()

    torch.cuda.set_device(dist.get_rank() % 8)
    device = torch.device(f"cuda:{dist.get_rank() % 8:d}")

    benchmarks = []
    if args.model:
        benchmarks.append(
            TorchvisionBenchmark(
                device=device,
                distributed_backend=args.distributed_backend,
                bucket_size=args.bucket_size,
                model=args.model,
            )
        )
    else:
        for model in ["resnet50", "resnet101", "resnext50_32x4d", "resnext101_32x8d"]:
            benchmarks.append(
                TorchvisionBenchmark(
                    device=device,
                    distributed_backend=args.distributed_backend,
                    bucket_size=args.bucket_size,
                    model=model,
                )
            )

    benchmark_results = []
    for benchmark in benchmarks:
        if args.rank == 0:
            print(f"\nBenchmark: {str(benchmark)}")
        result = sweep(benchmark)
        benchmark_results.append(
            {
                "model": benchmark.model,
                "batch_size": benchmark.batch_size,
                "result": result,
            }
        )

    # Write file with benchmark results if applicable
    if args.rank == 0 and args.json:
        report = {
            "pytorch_version": torch.__version__,
            "cuda_version": torch.version.cuda,
            "distributed_backend": args.distributed_backend,
            "bucket_size": args.bucket_size,
            "benchmark_results": benchmark_results,
        }
        with open(args.json, "w") as f:
            json.dump(report, f)