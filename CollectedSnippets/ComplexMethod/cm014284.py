def repro_analyze(options: Any, mod: nn.Module, load_args: Any) -> None:
    from torch._inductor.compile_fx import compile_fx_inner
    from torch._inductor.hooks import intermediate_hook

    mod, args = repro_common(options, mod, load_args)

    # TODO: The logic for cloning inputs/models here is intentionally
    # modeled off of run_fwd_maybe_bwd, but arguably it is better not to
    # clone inputs (as you are doubling your effective GPU memory usage).
    # It is certainly faster though!  It probably makes sense to let the
    # user specify the offload strategy.

    compile_args = _get_compile_args(mod, args)
    with tqdm(desc="Compiling"):
        compiled = compile_fx_inner(mod, compile_args)
    total = counters["inductor"]["intermediate_hooks"]

    known_names = set()

    def save_hook(name: str, val: Any) -> None:
        known_names.add(name)
        if not options.skip_saving_inductor_intermediates:
            writer.write_tensor(os.path.join("inductor", name), val)
        pbar.update(1)  # type: ignore[has-type]

    writer = torch.utils._content_store.ContentStoreWriter(
        options.save_dir, stable_hash=options.stable_hash
    )
    reader = torch.utils._content_store.ContentStoreReader(options.save_dir)

    new_args = clone_inputs(args)
    with (
        intermediate_hook(save_hook),
        tqdm(desc="Saving inductor intermediates", total=total) as pbar,
    ):
        assert not isinstance(compiled, str)
        compiled(new_args)  # type: ignore[arg-type]
        assert not new_args

    def compare_tuples(tuple1: tuple[Any], tuple2: tuple[Any]) -> str | None:
        diff_indices = [i for i in range(len(tuple1)) if tuple1[i] != tuple2[i]]
        diff_values = [(tuple1[i], tuple2[i]) for i in diff_indices]

        if not diff_values:
            return None
        else:
            return " and ".join(f"{a} != {b}" for a, b in diff_values)

    def check_hook(name: str, val: Any) -> None:
        meta = writer.compute_tensor_metadata(val)
        meta2 = reader.read_tensor_metadata(os.path.join("inductor", name))
        reason = compare_tuples(meta, meta2)
        if reason is not None:
            pbar.write(f"NONDETERMINISTIC INDUCTOR at {name} ({reason})")
        pbar.update(1)

    if not options.skip_check_deterministic:
        new_args = clone_inputs(args)
        with (
            intermediate_hook(check_hook),
            tqdm(desc="Checking inductor determinism", total=total) as pbar,
        ):
            compiled(new_args)  # type: ignore[arg-type]
            assert not new_args

    class WriterInterp(fx.Interpreter):
        def __init__(self, mod: torch.nn.Module, subdir: str) -> None:
            super().__init__(mod)
            self.subdir = subdir

        def run_node(self, n: torch.fx.Node) -> Any:
            r = super().run_node(n)
            name = n.name
            if name in known_names:
                pbar.update(1)
                writer.write_tensor(os.path.join(self.subdir, name), r)
            return r

    # NB: the module cast doesn't actually do anything, since there are no
    # parameters/buffers on the module
    if not options.skip_saving_float64_intermediates:
        new_mod, new_args = cast_to_fp64(copy.deepcopy(mod), clone_inputs(args))  # type: ignore[arg-type]
        with tqdm(desc="Saving float64 intermediates", total=total) as pbar:
            WriterInterp(new_mod, "float64").boxed_run(new_args)
        assert not new_args

    class ExactReaderInterp(fx.Interpreter):
        def run_node(self, n: torch.fx.Node) -> Any:
            r = super().run_node(n)
            name = n.name
            if name in known_names:
                meta = writer.compute_tensor_metadata(r)
                meta2 = reader.read_tensor_metadata(os.path.join("float64", name))
                reason = compare_tuples(meta, meta2)
                if reason is not None:
                    pbar.write(f"NONDETERMINISTIC FLOAT64 at {name} ({reason})")
                pbar.update(1)
            return r

    # TODO: check eager determinism

    if not options.skip_check_deterministic:
        new_mod, new_args = cast_to_fp64(copy.deepcopy(mod), clone_inputs(args))  # type: ignore[arg-type]
        with tqdm(desc="Checking float64 determinism", total=total) as pbar:
            ExactReaderInterp(new_mod).boxed_run(new_args)
            assert not new_args

    # Now that we've saved everything, interp through the eager graph
    # and do comparisons
    class ReaderInterp(fx.Interpreter):
        def run_node(self, n: torch.fx.Node) -> Any:
            r = super().run_node(n)
            name = n.name
            if name in known_names:
                inductor = reader.read_tensor(os.path.join("inductor", name))
                float64 = reader.read_tensor(os.path.join("float64", name))
                logged = False

                def log_error(msg: str, *args: Any) -> None:
                    nonlocal logged
                    logged = True
                    pbar.write(f"DIVERGED at {name}: {msg % args}")

                if not same(
                    r,
                    inductor,
                    float64,
                    tol=torch._dynamo.config.repro_tolerance,
                    equal_nan=True,
                    log_error=log_error,
                ):
                    assert logged
                pbar.update(1)
            return r

    with tqdm(desc="Checking divergence", total=total) as pbar:
        ReaderInterp(mod).boxed_run(args)
    assert not args