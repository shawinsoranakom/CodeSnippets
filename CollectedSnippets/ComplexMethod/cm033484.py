def main(self) -> None:
        """Main program entry point."""
        parser = argparse.ArgumentParser(description=__doc__)
        subparsers = parser.add_subparsers(metavar="COMMAND", required=True)

        for func in self.commands:
            func_parser = subparsers.add_parser(self._format_command_name(func), description=func.__doc__, help=func.__doc__)
            func_parser.set_defaults(func=func)

            exclusive_groups = {}
            signature = inspect.signature(func)

            for name in signature.parameters:
                if name not in self.arguments:
                    raise RuntimeError(f"The '{name}' argument, used by '{func.__name__}', has not been defined.")

                if (arguments := self.arguments.get(name)) is None:
                    continue  # internal use

                arguments = arguments.copy()
                exclusive = arguments.pop("exclusive", None)

                # noinspection PyProtectedMember, PyUnresolvedReferences
                command_parser: argparse._ActionsContainer

                if exclusive:
                    if exclusive not in exclusive_groups:
                        exclusive_groups[exclusive] = func_parser.add_mutually_exclusive_group()

                    command_parser = exclusive_groups[exclusive]
                else:
                    command_parser = func_parser

                if option_name := arguments.pop("name", None):
                    arguments.update(dest=name)
                else:
                    option_name = f"--{name.replace('_', '-')}"

                command_parser.add_argument(option_name, **arguments)

        try:
            # noinspection PyUnresolvedReferences
            import argcomplete
        except ImportError:
            pass
        else:
            argcomplete.autocomplete(parser)

        self.parsed_arguments = parser.parse_args()

        try:
            self.run(self.parsed_arguments.func)
        except ApplicationError as ex:
            display.fatal(ex)
            sys.exit(1)