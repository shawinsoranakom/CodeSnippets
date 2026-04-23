def run_model(args, model, inputs, key):
    rank = int(os.getenv("RANK", 0))
    world_size = int(os.getenv("WORLD_SIZE", 1))
    # result_q = []

    setup(rank, world_size)
    if args.device == "cuda":
        # needed for FSDP
        torch.cuda.set_device(rank)

    dev_rank = f"{args.device}:{rank}"
    model = model.to(dev_rank)

    def move_tensor(maybe_tensor):
        if torch.is_tensor(maybe_tensor):
            return maybe_tensor.to(dev_rank)
        return maybe_tensor

    inputs = pytree.tree_map(move_tensor, inputs)

    if args.fsdp:
        model = apply_fsdp(
            args,
            model,
            use_checkpointing=args.fsdp_checkpoint,
            use_wrap_policy=args.fsdp_wrap,
        )
    elif args.ddp:
        model = DDP(model)

    if args.verbose:
        print(model)

    if args.dynamo:
        dynamo.reset()
        if args.verbose:
            dynamo.config.verbose = True
            dynamo.config.log_level = logging.DEBUG
        if args.dynamo_no_optimize_ddp:
            dynamo.config.optimize_ddp = False
        if args.dynamo == "inductor" and args.fsdp:
            torch._inductor.config.triton.cudagraphs = False
            log.warning("disabling inductor cudagraphs for compatibility with FSDP")

        def print_compile(gm, ex):
            print(
                f"print_compile:\n{str(gm.graph)}\n-----------------------------------------"
            )
            return gm

        dynamo_ctx = dynamo.optimize(
            print_compile if args.dynamo == "print" else args.dynamo
        )
        model = dynamo_ctx(model)

    # warmup
    _ = timed(model, model_iter_fn, inputs, times=3, return_result=False)
    t_total = timed(
        model, model_iter_fn, inputs, times=args.repeat, return_result=False
    )
    if args.torchviz:
        torchviz_model(args, model, inputs, rank)
    if args.profile:
        profile_model(args, model, inputs, rank)

    cleanup()
    return t_total