def main():
    args = parse_args()
    cfg = BenchConfig(
        use_cuda_graph=not args.no_cuda_graph,
        warmup=args.warmup,
        rep=args.rep,
    )

    torch.set_default_device(current_platform.device_type)

    metadata = collect_env_metadata(cfg)
    print_metadata(metadata)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    save_dir = args.save_path or os.path.join(
        tempfile.gettempdir(), f"vllm_ir_bench_{timestamp}"
    )
    os.makedirs(save_dir, exist_ok=True)

    op_filters = [f.strip() for f in args.ops.split(",")] if args.ops else None
    all_summary_rows: list[dict[str, str]] = []

    for op in IrOp.registry.values():
        if op_filters and not any(f in op.name for f in op_filters):
            continue
        if not op.has_input_generator:
            print(f"Skipping op '{op.name}': no input generator registered")
            continue
        if op.name not in SHAPE_CONFIGS:
            raise RuntimeError(
                f"No benchmark shape config for op '{op.name}'. "
                f"Add it to benchmarks/kernels/ir/shapes.py"
            )

        case_names, providers, results = collect_timings(
            op, SHAPE_CONFIGS[op.name], cfg
        )
        detail_rows, summary_rows, header_cols = analyze_results(
            op.name, case_names, providers, results
        )
        all_summary_rows.extend(summary_rows)

        save_results(
            save_dir,
            op.name,
            detail_rows,
            header_cols,
            all_summary_rows,
            metadata,
        )

    print(f"\nResults saved to: {save_dir}")