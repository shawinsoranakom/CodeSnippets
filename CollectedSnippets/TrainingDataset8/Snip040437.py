def run_test(
    ctx: Context,
    specpath: str,
    streamlit_command: List[str],
    show_output: bool = False,
) -> bool:
    """Run a single e2e test.

     An e2e test consists of a Streamlit script that produces a result, and
     a Cypress test file that asserts that result is as expected.

    Parameters
    ----------
    ctx : Context
        The Context object that contains our global testing parameters.
    specpath : str
        The path of the Cypress spec file to run.
    streamlit_command : list of str
        The Streamlit command to run (passed directly to subprocess.Popen()).

    Returns
    -------
    bool
        True if the test succeeded.

    """
    SUCCESS = "SUCCESS"
    RETRY = "RETRY"
    SKIP = "SKIP"
    QUIT = "QUIT"

    result = None

    # Move existing credentials file aside, and create a new one if the
    # tests call for it.
    with move_aside_file(CREDENTIALS_FILE):
        create_credentials_toml('[general]\nemail="test@streamlit.io"')

        # Loop until the test succeeds or is skipped.
        while result not in (SUCCESS, SKIP, QUIT):
            cypress_command = ["yarn", "cy:run", "--spec", specpath]
            cypress_command.extend(["--reporter", "cypress-circleci-reporter"])
            cypress_command.extend(ctx.cypress_flags)

            click.echo(
                f"{click.style('Running test:', fg='yellow', bold=True)}"
                f"\n{click.style(' '.join(streamlit_command), fg='yellow')}"
                f"\n{click.style(' '.join(cypress_command), fg='yellow')}"
            )

            # Start the streamlit command
            with AsyncSubprocess(streamlit_command, cwd=FRONTEND_DIR) as streamlit_proc:
                # Run the Cypress spec to completion.
                cypress_result = subprocess.run(
                    cypress_command,
                    cwd=FRONTEND_DIR,
                    capture_output=True,
                    text=True,
                )

                # Terminate the streamlit command and get its output
                streamlit_stdout = streamlit_proc.terminate()

            def print_output():
                click.echo(
                    f"\n\n{click.style('Streamlit output:', fg='yellow', bold=True)}"
                    f"\n{streamlit_stdout}"
                    f"\n\n{click.style('Cypress output:', fg='yellow', bold=True)}"
                    f"\n{cypress_result.stdout}"
                    f"\n"
                )

            if cypress_result.returncode == 0:
                result = SUCCESS
                click.echo(click.style("Success!\n", fg="green", bold=True))
                if show_output:
                    print_output()
            else:
                # The test failed. Print the output of the Streamlit command
                # and the Cypress command.
                click.echo(click.style("Failure!", fg="red", bold=True))
                print_output()

                if ctx.always_continue:
                    result = SKIP
                else:
                    # Prompt the user for what to do next.
                    user_input = click.prompt(
                        "[R]etry, [U]pdate snapshots, [S]kip, or [Q]uit?",
                        default="r",
                    )
                    key = user_input[0].lower()
                    if key == "s":
                        result = SKIP
                    elif key == "q":
                        result = QUIT
                    elif key == "r":
                        result = RETRY
                    elif key == "u":
                        ctx.update_snapshots = True
                        result = RETRY
                    else:
                        # Retry if key not recognized
                        result = RETRY

    if result != SUCCESS:
        ctx.any_failed = True

    if result == QUIT:
        raise QuitException()

    return result == SUCCESS