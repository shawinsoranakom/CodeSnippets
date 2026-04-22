def run_commands(section_header, commands, skip_last_input=False, comment=None):
    """Run a list of commands, displaying them within the given section."""
    global auto_run

    for i, command in enumerate(commands):
        # Display the status.
        vars = {
            "section_header": section_header,
            "total": len(commands),
            "command": command,
            "v": i + 1,
        }
        click.secho(
            "\nRunning %(section_header)s %(v)s/%(total)s : %(command)s" % vars,
            bold=True,
        )
        click.secho("\n%(v)s/%(total)s : %(command)s" % vars, fg="yellow", bold=True)

        if comment:
            click.secho(comment)

        # Run the command.
        os.system(command)

        last_command = i + 1 == len(commands)
        if not (auto_run or (last_command and skip_last_input)):
            click.secho(
                "Press [enter] to continue or [a] to continue on auto:\n> ", nl=False
            )
            response = click.getchar()
            if response == "a":
                print("Turning on auto run.")
                auto_run = True