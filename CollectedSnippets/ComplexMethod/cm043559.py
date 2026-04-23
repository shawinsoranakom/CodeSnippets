def parse_known_args_and_warn(  # pylint: disable=R0917
        cls,
        parser: argparse.ArgumentParser,
        other_args: list[str],
        export_allowed: Literal[
            "no_export", "raw_data_only", "figures_only", "raw_data_and_figures"
        ] = "no_export",
        raw: bool = False,
        limit: int = 0,
    ):
        """Parse list of arguments into the supplied parser.

        Parameters
        ----------
        parser: argparse.ArgumentParser
            Parser with predefined arguments
        other_args: List[str]
            list of arguments to parse
        export_allowed: Literal["no_export", "raw_data_only", "figures_only", "raw_data_and_figures"]
            Export options
        raw: bool
            Add the --raw flag
        limit: int
            Add a --limit flag with this number default

        Returns
        ----------
        ns_parser:
            Namespace with parsed arguments
        """
        parser.add_argument(
            "-h", "--help", action="store_true", help="show this help message"
        )

        if export_allowed != "no_export":
            choices_export = []
            help_export = "Does not export!"

            if export_allowed == "raw_data_only":
                choices_export = ["csv", "json", "xlsx"]
                help_export = "Export raw data into csv, json or xlsx."
            elif export_allowed == "figures_only":
                choices_export = ["png", "jpg"]
                help_export = "Export figure into png or jpg."
            else:
                choices_export = ["csv", "json", "xlsx", "png", "jpg"]
                help_export = (
                    "Export raw data into csv, json, xlsx and figure into png or jpg."
                )

            parser.add_argument(
                "--export",
                default="",
                type=check_file_type_saved(choices_export),
                dest="export",
                help=help_export,
                nargs="+",
            )

            # If excel is an option, add the sheet name
            if export_allowed in [
                "raw_data_only",
                "raw_data_and_figures",
            ]:
                parser.add_argument(
                    "--sheet-name",
                    dest="sheet_name",
                    default=None,
                    nargs="+",
                    help="Name of excel sheet to save data to. Only valid for .xlsx files.",
                )

        if raw:
            parser.add_argument(
                "--raw",
                dest="raw",
                action="store_true",
                default=False,
                help="Flag to display raw data",
            )
        if limit > 0:
            parser.add_argument(
                "-l",
                "--limit",
                dest="limit",
                default=limit,
                help="Number of entries to show in data.",
                type=check_positive,
            )

        parser.add_argument(
            "--register_obbject",
            dest="register_obbject",
            action="store_false",
            default=True,
            help="Flag to store data in the OBBject registry, True by default.",
        )
        parser.add_argument(
            "--register_key",
            dest="register_key",
            default="",
            help="Key to reference data in the OBBject registry.",
            type=validate_register_key,
        )

        if session.settings.USE_CLEAR_AFTER_CMD:
            system_clear()

        if "--help" in other_args or "-h" in other_args:
            txt_help = parser.format_help() + "\n"
            session.console.print(f"[help]{txt_help}[/help]")
            return None

        try:
            # Determine the index of the routine arguments
            routine_args_index = next(
                (
                    i + 1
                    for i, arg in enumerate(other_args)
                    if arg in ("-i", "--input")
                    and "routine_args"
                    in [
                        action.dest
                        for action in parser._actions  # pylint: disable=protected-access
                    ]
                ),
                -1,
            )
            # Collect indices whose values should NOT be comma-split because
            # the provider may accept a comma-separated string (e.g. --symbol
            # AAPL,MSFT).  Handles --flag value, --flag=value, -f value, and
            # multi-value flags (nargs="+" / nargs="*" / nargs=N).
            no_split_indices: set[int] = set()
            if 0 <= routine_args_index < len(other_args):
                no_split_indices.add(routine_args_index)

            for i, arg in enumerate(other_args):
                if not arg.startswith("-"):
                    continue
                # Handle --flag=value by extracting the flag portion.
                flag_part = arg.split("=", 1)[0] if "=" in arg else arg
                for action in parser._actions:  # pylint: disable=protected-access
                    if flag_part in action.option_strings and action.nargs != 0:
                        if "=" in arg:
                            # Value is embedded in the same token.
                            no_split_indices.add(i)
                        elif action.nargs in ("+", "*") or (
                            isinstance(action.nargs, int) and action.nargs > 1
                        ):
                            # Multi-value flag: protect all consecutive
                            # non-flag tokens after the flag.
                            j = i + 1
                            while j < len(other_args) and not other_args[j].startswith(
                                "-"
                            ):
                                no_split_indices.add(j)
                                j += 1
                        # Single-value flag: protect the next token.
                        elif i + 1 < len(other_args):
                            no_split_indices.add(i + 1)
                        break

            # Split comma-separated arguments only for positional / unflagged values.
            other_args = [
                part
                for index, arg in enumerate(other_args)
                for part in ([arg] if index in no_split_indices else arg.split(","))
            ]

            # Check if the action has optional choices, if yes, remove them
            for action in parser._actions:  # pylint: disable=protected-access
                if getattr(action, "optional_choices", None):
                    action.choices = None

            ns_parser, l_unknown_args = parser.parse_known_args(other_args)

            if export_allowed in [
                "raw_data_only",
                "raw_data_and_figures",
            ]:
                ns_parser.is_image = any(
                    ext in ns_parser.export for ext in ["png", "jpg"]
                )

        except SystemExit:
            # In case the command has required argument that isn't specified

            return None

        if l_unknown_args:
            session.console.print(
                f"The following args couldn't be interpreted: {l_unknown_args}"
            )
        return ns_parser