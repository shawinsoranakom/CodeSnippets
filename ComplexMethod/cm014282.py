def save_graph_repro(
    fd: IO[Any],
    gm: torch.fx.GraphModule,
    args: Sequence[Any],
    compiler_name: str,
    *,
    stable_output: bool = False,
    save_dir: str | None = None,
    command: str = "run",
    accuracy: str | bool | None = None,
    tracing_mode: str | None = None,
    check_str: str | None = None,
    stable_hash: bool = False,
) -> None:
    if any(
        isinstance(arg, torch.fx.experimental._backward_state.BackwardState)
        for arg in args
    ):
        fd.write(
            "Repro is not generated due to existence of BackwardState in graph input"
        )
        return

    if save_dir is not None:
        save_dir = normalize_path_separator(save_dir)

    # Extract distributed info from the graph
    distributed_info = _extract_distributed_info(gm)
    has_distributed_ops = len(distributed_info) > 0

    fd.write(
        generate_compiler_repro_string(
            gm,
            args,
            stable_output=stable_output,
            save_dir=save_dir,
            stable_hash=stable_hash,
            has_distributed_ops=has_distributed_ops,
        )
    )
    if accuracy is None:
        accuracy = "_accuracy" in compiler_name
    if tracing_mode is None:
        tracing_mode = "real"
        if any(
            has_free_symbols(a) for a in args if not isinstance(a, FakeScriptObject)
        ):
            tracing_mode = "symbolic"
    fd.write("if __name__ == '__main__':\n")
    fd.write("    from torch._dynamo.repro.after_aot import run_repro\n")

    # Add distributed initialization before run_repro if needed
    if has_distributed_ops:
        fd.write(
            "    from torch._dynamo.repro.after_aot import setup_fake_process_groups\n"
        )
        fd.write(f"    setup_fake_process_groups({distributed_info!r})\n")

    fd.write(
        f"    with torch.no_grad():\n"
        f"        run_repro(mod, load_args, accuracy={accuracy!r}, command={command!r}, "
        f"save_dir={save_dir!r}, tracing_mode={tracing_mode!r}, check_str={check_str!r})\n"
        f"        # To run it separately, do \n"
        f"        # mod, args = run_repro(mod, load_args, accuracy={accuracy!r}, command='get_args', "
        f"save_dir={save_dir!r}, tracing_mode={tracing_mode!r}, check_str={check_str!r})\n"
        f"        # mod(*args)"
    )

    # Add distributed cleanup after run_repro
    if has_distributed_ops:
        fd.write("\n    dist.destroy_process_group()\n")