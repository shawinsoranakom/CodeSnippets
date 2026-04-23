def run_cli(jobs_cmds: list[str] | None = None, test_mode=False):
    """Run the CLI menu."""
    ret_code = 1
    t_controller = CLIController(jobs_cmds)
    an_input = ""

    jobs_cmds = handle_job_cmds(jobs_cmds)

    bootup()
    if not jobs_cmds:
        welcome_message()

        if first_time_user():
            with contextlib.suppress(EOFError):
                webbrowser.open("https://docs.openbb.co/cli")

        t_controller.print_help()

    while ret_code:
        # There is a command in the queue
        if t_controller.queue and len(t_controller.queue) > 0:
            # If the command is quitting the menu we want to return in here
            if t_controller.queue[0] in ("q", "..", "quit"):
                print_goodbye()
                break

            # Consume 1 element from the queue
            an_input = t_controller.queue[0]
            t_controller.queue = t_controller.queue[1:]

            # Print the current location because this was an instruction and we want user to know what was the action
            if an_input and an_input.split(" ")[0] in t_controller.CHOICES_COMMANDS:
                session.console.print(f"{get_flair_and_username()} / $ {an_input}")

        # Get input command from user
        else:
            try:
                # Get input from user using auto-completion
                if session.prompt_session and session.settings.USE_PROMPT_TOOLKIT:
                    # Check if toolbar hint was enabled
                    if session.settings.TOOLBAR_HINT:
                        an_input = session.prompt_session.prompt(  # type: ignore[union-attr]
                            f"{get_flair_and_username()} / $ ",
                            completer=t_controller.completer,
                            search_ignore_case=True,
                            bottom_toolbar=HTML(
                                '<style bg="ansiblack" fg="ansiwhite">[h]</style> help menu    '
                                '<style bg="ansiblack" fg="ansiwhite">[q]</style> return to previous menu    '
                                '<style bg="ansiblack" fg="ansiwhite">[e]</style> exit the program    '
                                '<style bg="ansiblack" fg="ansiwhite">[cmd -h]</style> '
                                "see usage and available options    "
                            ),
                            style=Style.from_dict(
                                {
                                    "bottom-toolbar": "#ffffff bg:#333333",
                                }
                            ),
                        )
                    else:
                        an_input = session.prompt_session.prompt(  # type: ignore[union-attr]
                            f"{get_flair_and_username()} / $ ",
                            completer=t_controller.completer,
                            search_ignore_case=True,
                        )

                # Get input from user without auto-completion
                else:
                    an_input = input(f"{get_flair_and_username()} / $ ")

            except (KeyboardInterrupt, EOFError):
                print_goodbye()
                break

        try:
            # Process the input command
            t_controller.queue = t_controller.switch(an_input)

            if an_input in ("q", "quit", "..", "exit", "e"):
                print_goodbye()
                break

            # Check if the user wants to reset application
            if an_input in ("r", "reset") or t_controller.update_success:
                reset(t_controller.queue if t_controller.queue else [])
                break

        except SystemExit:
            session.console.print(
                f"[red]The command '{an_input}' doesn't exist on the / menu.[/red]\n",
            )
            similar_cmd = difflib.get_close_matches(
                an_input.split(" ")[0] if " " in an_input else an_input,
                t_controller.controller_choices,
                n=1,
                cutoff=0.7,
            )
            if similar_cmd:
                an_input = similar_cmd[0]
                if " " in an_input:
                    candidate_input = (
                        f"{similar_cmd[0]} {' '.join(an_input.split(' ')[1:])}"
                    )
                    if candidate_input == an_input:
                        an_input = ""
                        t_controller.queue = []
                        session.console.print("\n")
                        continue
                    an_input = candidate_input

                session.console.print(f"[green]Replacing by '{an_input}'.[/green]")
                t_controller.queue.insert(0, an_input)