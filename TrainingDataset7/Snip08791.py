def check_programs(*programs):
    for program in programs:
        if find_command(program) is None:
            raise CommandError(
                f"Can't find {program}. Make sure you have GNU gettext tools "
                "0.19 or newer installed."
            )