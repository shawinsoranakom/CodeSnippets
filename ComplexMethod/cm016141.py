def cmd_prepare_repro(args):
    suites = set()
    if args.suite:
        suite = SUITE_ALIASES.get(args.suite, args.suite)
        suites = {suite}
    else:
        suites = {"huggingface", "timm_models", "torchbench"}

    torchbench_pin = read_pin("torchbench.txt")
    timm_pin = read_pin("timm.txt")
    hf_reqs = read_pin("huggingface-requirements.txt")

    print("# Setup commands for inductor perf benchmark suites")
    print("# These mirror what CI does in the inductor-benchmarks Docker image.")
    print("#")
    print("# Pinned versions (commits, package versions) are read live from")
    print("#   .ci/docker/ci_commit_pins/")
    print("# Install steps are based on:")
    print("#   .ci/docker/common/install_inductor_benchmark_deps.sh  (build-time)")
    print("#   .ci/pytorch/test.sh                                   (runtime)")
    print("# If the setup process changes, check those files.")
    print()

    if "huggingface" in suites:
        print("# ── HuggingFace ──")
        for line in hf_reqs.splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                print(f"pip install {line}")
        print()

    if "timm_models" in suites:
        print("# ── Timm ──")
        print(
            f"pip install git+https://github.com/huggingface/pytorch-image-models@{timm_pin}"
        )
        print()

    if "torchbench" in suites:
        print("# ── TorchBench ──")
        print("git clone https://github.com/pytorch/benchmark torchbench")
        print(f"cd torchbench && git checkout {torchbench_pin}")
        print("python install.py --continue_on_fail")
        print("cd ..")
        print()
        print("# Set PYTHONPATH so benchmark scripts find torchbench")
        print("export PYTHONPATH=$(pwd)/torchbench")
        print()

    print("# ── Runtime dependencies ──")
    print("pip install torchvision torchaudio")
    if "torchbench" in suites:
        print("pip install opencv-python==4.8.0.74")
    print()

    print("# ── Environment variables ──")
    print("export TORCHINDUCTOR_FX_GRAPH_CACHE=True")
    print("export TORCHINDUCTOR_AUTOGRAD_CACHE=True")
    print()

    if not args.no_repro:
        # Also print repro commands if we have a run_id
        if args.run_id:
            # Reuse the repro logic
            repro_args = argparse.Namespace(
                run_id=args.run_id,
                device=args.device,
                model=args.model,
                suite=args.suite,
                mode=args.mode,
                backend=None,
                dtype=None,
                runtime=None,
                attempt=args.attempt,
            )
            print("# ── Benchmark commands ──")
            cmd_repro(repro_args)