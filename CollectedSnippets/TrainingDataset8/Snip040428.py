def run_commands(section_header, commands):
    """Run a list of commands, displaying them within the given section."""

    pool = ThreadPool(processes=4)
    lock = Lock()
    failed_commands = []

    def process_command(arg):
        i, command = arg

        # Display the status.
        vars = {
            "section_header": section_header,
            "total": len(commands),
            "command": _command_to_string(command),
            "v": i + 1,
        }
        click.secho(
            "\nRunning %(section_header)s %(v)s/%(total)s : %(command)s" % vars,
            bold=True,
        )

        # Run the command.
        result = subprocess.call(
            command.split(" "), stdout=subprocess.DEVNULL, stderr=None
        )
        if result != 0:
            with lock:
                failed_commands.append(command)

    pool.map(process_command, enumerate(commands))
    return failed_commands