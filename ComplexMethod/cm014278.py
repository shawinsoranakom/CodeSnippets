def save_graph_repro_ep(
    fd: IO[Any],
    compiler_name: str,
    *,
    exported_program: ExportedProgram | None = None,
    gm: torch.nn.Module | None = None,
    args: tuple[Any] | None = None,
    config_patches: dict[str, str] | None = None,
    stable_output: bool = False,
    save_dir: str | None = None,
    command: str = "run",
    accuracy: str | bool | None = None,
    check_str: str | None = None,
    module_in_comment: bool = False,
    strict: bool = False,
) -> None:
    # Save graph for reproducing the error.
    # Either exported_program or gm will be saved, depending on which one is defined.
    # Only one of exported_program and gm should be defined.

    if exported_program is None and gm is None:
        raise AOTIMinifierError("One of exported_program and gm must be defined")
    if exported_program is not None and gm is not None:
        raise AOTIMinifierError("Only one of exported_program and gm can be defined")
    if gm is not None and args is None:
        raise AOTIMinifierError("If gm is defined, args should also be defined")

    if exported_program is None:
        assert gm is not None
        assert args is not None
        exported_program = torch.export.export(gm, args, strict=strict)
    elif gm is None:
        gm = exported_program.module(check_guards=False)

    # save a graph preview using gm
    module_string = get_module_string(gm)  # type: ignore[arg-type]
    fd.write(module_string)

    # save a graph repro using exported_program
    fd.write(
        generate_compiler_repro_exported_program(
            exported_program,
            options=config_patches,
            stable_output=stable_output,
            save_dir=save_dir,
        )
    )
    if accuracy is None:
        accuracy = "_accuracy" in compiler_name
    fd.write("if __name__ == '__main__':\n")
    fd.write("    from torch._dynamo.repro.aoti import run_repro\n")
    fd.write(
        f"    with torch.no_grad():\n"
        f"        run_repro(exported_program, config_patches=config_patches, accuracy={accuracy!r}, command={command!r}, "
        f"save_dir={save_dir!r}, check_str={check_str!r})\n"
    )