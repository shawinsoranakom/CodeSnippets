def call_stop(self, other_args) -> None:
        """Process stop command."""
        parser = argparse.ArgumentParser(
            add_help=False,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            prog="stop",
            description="Stop recording session into .openbb routine file",
        )
        # This is only for auto-completion purposes
        _, _ = self.parse_simple_args(parser, other_args)

        if "-h" not in other_args and "--help" not in other_args:
            global RECORD_SESSION  # noqa: PLW0603
            global SESSION_RECORDED  # noqa: PLW0603

            if not RECORD_SESSION:
                session.console.print(
                    "[red]There is no session being recorded. Start one using the command 'record'[/red]\n"
                )
            elif len(SESSION_RECORDED) < 5:
                session.console.print(
                    "[red]Run at least 4 commands before stopping recording a session.[/red]\n"
                )
            else:
                current_user = session.user
                title_for_local_storage = (
                    SESSION_RECORDED_NAME.replace(" ", "_") + ".openbb"
                )

                routine_file = os.path.join(
                    f"{current_user.preferences.export_directory}/routines",
                    title_for_local_storage,
                )

                # If file already exists, add a timestamp to the name
                if os.path.isfile(routine_file):
                    i = session.console.input(
                        "A local routine with the same name already exists, do you want to override it? (y/n): "
                    )
                    session.console.print("")
                    while i.lower() not in ["y", "yes", "n", "no"]:
                        i = session.console.input("Select 'y' or 'n' to proceed: ")
                        session.console.print("")

                    if i.lower() in ["n", "no"]:
                        new_name = (
                            datetime.now().strftime("%Y%m%d_%H%M%S_")
                            + title_for_local_storage
                        )
                        routine_file = os.path.join(
                            current_user.preferences.export_directory,
                            "routines",
                            new_name,
                        )
                        session.console.print(
                            f"[yellow]The routine name has been updated to '{new_name}'[/yellow]\n"
                        )

                # Writing to file
                Path(os.path.dirname(routine_file)).mkdir(parents=True, exist_ok=True)

                with open(routine_file, "w") as file1:
                    lines = ["# OpenBB Platform CLI - Routine", "\n"]
                    lines += [
                        f"# Title: {SESSION_RECORDED_NAME}",
                        "\n",
                        f"# Tags: {SESSION_RECORDED_TAGS}",
                        "\n\n",
                        f"# Description: {SESSION_RECORDED_DESCRIPTION}",
                        "\n\n",
                    ]
                    lines += [c + "\n" for c in SESSION_RECORDED[:-1]]
                    # Writing data to a file
                    file1.writelines(lines)

                session.console.print(
                    f"[green]Your routine has been recorded and saved here: {routine_file}[/green]\n"
                )

                # Clear session to be recorded again
                RECORD_SESSION = False
                SESSION_RECORDED = list()