def _run_lintrunner(
    default_linters,
    take,
    skip,
    apply_patches=False,
    all_files=False,
    lintrunner_args=None,
    return_json_output=False,
):
    cmd = LINTRUNNER_BASE_CMD
    if return_json_output:
        tee_file = mktemp(prefix="spinlint_", suffix=".json")
        tee_cmd = ["--tee-json", tee_file]
    else:
        tee_file = None
        tee_cmd = []
    linters = default_linters.copy()
    if take is not None:
        linters &= take
    if skip is not None:
        linters -= skip
    if not linters:
        click.echo("No linters to run after applying --take/--skip filters.")
        click.echo("Skipping lintrunner execution.")
        lint_found = False
        if return_json_output:
            json_output = ""
        else:
            json_output = None
    else:
        full_cmd = (
            cmd
            + tee_cmd
            + [
                "--take",
                ",".join(linters),
            ]
            + (["--apply-patches"] if apply_patches else [])
            + (["--all-files"] if all_files else [])
            + (list(lintrunner_args) if lintrunner_args else [])
        )
        p = spin.util.run(full_cmd, sys_exit=False)
        lint_found = bool(p.returncode)
        if tee_file:
            tee_path = Path(tee_file)
            json_output = tee_path.read_text()
            tee_path.unlink()
        else:
            json_output = None
    return lint_found, json_output