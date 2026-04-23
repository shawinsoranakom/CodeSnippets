def run_scripts(  # pylint: disable=R0917
    path: Path,
    test_mode: bool = False,
    verbose: bool = False,
    routines_args: list[str] | None = None,
    special_arguments: dict[str, str] | None = None,
    output: bool = True,
):
    """Run given .openbb scripts.

    Parameters
    ----------
    path : str
        The location of the .openbb file
    test_mode : bool
        Whether the CLI is in test mode
    verbose : bool
        Whether to run tests in verbose mode
    routines_args : List[str]
        One or multiple inputs to be replaced in the routine and separated by commas.
        E.g. GME,AMC,BTC-USD
    special_arguments: Optional[Dict[str, str]]
        Replace `${key=default}` with `value` for every key in the dictionary
    output: bool
        Whether to log tests to txt files
    """
    if not path.exists():
        session.console.print(f"File '{path}' doesn't exist. Launching base CLI.\n")
        if not test_mode:
            run_cli()

    with path.open() as fp:
        raw_lines = [x for x in fp if (not is_reset(x)) and ("#" not in x) and x]
        raw_lines = [
            raw_line.strip("\n") for raw_line in raw_lines if raw_line.strip("\n")
        ]

        if routines_args:
            lines = []
            for rawline in raw_lines:
                templine = rawline
                for i, arg in enumerate(routines_args):
                    templine = templine.replace(f"$ARGV[{i}]", arg)
                lines.append(templine)
        # Handle new testing arguments:
        elif special_arguments:
            lines = []
            for line in raw_lines:
                new_line = re.sub(
                    r"\${[^{]+=[^{]+}",
                    lambda x: replace_dynamic(x, special_arguments),  # type: ignore
                    line,
                )
                lines.append(new_line)

        else:
            lines = raw_lines

        if test_mode and "exit" not in lines[-1]:
            lines.append("exit")

        # Deals with the export with a path with "/" in it
        export_folder = ""
        if "export" in lines[0]:
            export_folder = lines[0].split("export ")[1].rstrip()
            lines = lines[1:]

        simulate_argv = f"/{'/'.join([line.rstrip() for line in lines])}"
        file_cmds = simulate_argv.replace("//", "/home/").split()
        file_cmds = insert_start_slash(file_cmds) if file_cmds else file_cmds
        file_cmds = (
            [f"export {export_folder}{' '.join(file_cmds)}"]
            if export_folder
            else [" ".join(file_cmds)]
        )

        if not test_mode or verbose:
            run_cli(file_cmds, test_mode=True)
        else:
            with suppress_stdout():
                session.console.print(f"To ensure: {output}")
                if output:
                    timestamp = datetime.now().timestamp()
                    stamp_str = str(timestamp).replace(".", "")
                    whole_path = Path(REPOSITORY_DIRECTORY / "integration_test_output")
                    whole_path.mkdir(parents=True, exist_ok=True)
                    first_cmd = file_cmds[0].split("/")[1]
                    with (
                        open(
                            whole_path / f"{stamp_str}_{first_cmd}_output.txt", "w"
                        ) as output_file,
                        contextlib.redirect_stdout(output_file),
                    ):
                        run_cli(file_cmds, test_mode=True)
                else:
                    run_cli(file_cmds, test_mode=True)