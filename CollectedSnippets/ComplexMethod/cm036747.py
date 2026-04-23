def _validate_args(args: argparse.Namespace):
    if args.quant_dtype is not None:
        assert args.quant_dtype == torch.float8_e4m3fn
        if args.block_shape is not None:
            assert len(args.block_shape) == 2, (
                f"block shape must have 2 elements. got {args.block_shape}"
            )

    if args.experts_type in MK_SINGLE_GPU_PREPARE_FINALIZE_TYPES:
        assert args.world_size == 1, "Single GPU objects need world size set to 1"

    if args.torch_trace_dir_path is not None:
        from pathlib import Path

        assert Path(args.torch_trace_dir_path).is_dir(), (
            f"Please create {args.torch_trace_dir_path}"
        )