def call_record(self, other_args) -> None:
        """Process record command."""
        parser = argparse.ArgumentParser(
            add_help=False,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            prog="record",
            description="Start recording session into .openbb routine file",
        )
        parser.add_argument(
            "-n",
            "--name",
            action="store",
            dest="name",
            type=str,
            default="",
            help="Routine title name to be saved - only use characters, digits and whitespaces.",
            nargs="+",
        )
        parser.add_argument(
            "-d",
            "--description",
            type=str,
            dest="description",
            help="The description of the routine",
            default=f"Routine recorded at {datetime.now().strftime('%H:%M')} from the OpenBB Platform CLI",
            nargs="+",
        )
        parser.add_argument(
            "--tag1",
            type=str,
            dest="tag1",
            help=f"The tag associated with the routine. Select from: {', '.join(SCRIPT_TAGS)}",
            default="",
            nargs="+",
        )
        parser.add_argument(
            "--tag2",
            type=str,
            dest="tag2",
            help=f"The tag associated with the routine. Select from: {', '.join(SCRIPT_TAGS)}",
            default="",
            nargs="+",
        )
        parser.add_argument(
            "--tag3",
            type=str,
            dest="tag3",
            help=f"The tag associated with the routine. Select from: {', '.join(SCRIPT_TAGS)}",
            default="",
            nargs="+",
        )
        parser.add_argument(
            "-p",
            "--public",
            dest="public",
            action="store_true",
            help="Whether the routine should be public or not",
            default=False,
        )

        if other_args and "-" not in other_args[0][0]:
            other_args.insert(0, "-n")

        ns_parser, _ = self.parse_simple_args(parser, other_args)

        if ns_parser:
            if not ns_parser.name:
                session.console.print(
                    "[red]Set a routine title by using the '-n' flag. E.g. 'record -n Morning routine'[/red]"
                )
                return

            tag1 = (
                " ".join(ns_parser.tag1)
                if isinstance(ns_parser.tag1, list)
                else ns_parser.tag1
            )
            if tag1 and tag1 not in SCRIPT_TAGS:
                session.console.print(
                    f"[red]The parameter 'tag1' needs to be one of the following {', '.join(SCRIPT_TAGS)}[/red]"
                )
                return

            tag2 = (
                " ".join(ns_parser.tag2)
                if isinstance(ns_parser.tag2, list)
                else ns_parser.tag2
            )
            if tag2 and tag2 not in SCRIPT_TAGS:
                session.console.print(
                    f"[red]The parameter 'tag2' needs to be one of the following {', '.join(SCRIPT_TAGS)}[/red]"
                )
                return

            tag3 = (
                " ".join(ns_parser.tag3)
                if isinstance(ns_parser.tag3, list)
                else ns_parser.tag3
            )
            if tag3 and tag3 not in SCRIPT_TAGS:
                session.console.print(
                    f"[red]The parameter 'tag3' needs to be one of the following {', '.join(SCRIPT_TAGS)}[/red]"
                )
                return

            # Check if title has a valid format
            title = " ".join(ns_parser.name) if ns_parser.name else ""
            pattern = re.compile(r"^[a-zA-Z0-9\s]+$")
            if not pattern.match(title):
                session.console.print(
                    f"[red]Title '{title}' has invalid format. Please use only digits, characters and whitespaces.[/]"
                )
                return

            global RECORD_SESSION  # noqa: PLW0603
            global SESSION_RECORDED_NAME  # noqa: PLW0603
            global SESSION_RECORDED_DESCRIPTION  # noqa: PLW0603
            global SESSION_RECORDED_TAGS  # noqa: PLW0603
            global SESSION_RECORDED_PUBLIC  # noqa: PLW0603

            RECORD_SESSION = True
            SESSION_RECORDED_NAME = title
            SESSION_RECORDED_DESCRIPTION = (
                " ".join(ns_parser.description)
                if isinstance(ns_parser.description, list)
                else ns_parser.description
            )
            SESSION_RECORDED_TAGS = tag1 if tag1 else ""
            SESSION_RECORDED_TAGS += "," + tag2 if tag2 else ""
            SESSION_RECORDED_TAGS += "," + tag3 if tag3 else ""

            SESSION_RECORDED_PUBLIC = ns_parser.public

            session.console.print(
                f"[green]The routine '{title}' is successfully being recorded.[/green]"
            )
            session.console.print(
                "\n[yellow]Remember to run 'stop' command when you are done!\n[/yellow]"
            )