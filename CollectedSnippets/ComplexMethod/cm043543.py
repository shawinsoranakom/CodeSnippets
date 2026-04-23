def _set(self, other_args: list[str], field=field) -> None:
            """Set preference value."""
            field_name = field["field_name"]
            annotation = field["annotation"]
            command = field["command"]
            type_ = str if get_origin(annotation) is Literal else annotation
            choices = None
            if get_origin(annotation) is Literal:
                choices = annotation.__args__
            elif command == "console_style":
                # To have updated choices for console style
                choices = session.style.available_styles
            parser = argparse.ArgumentParser(
                formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                prog=command,
                description=field["description"],
                add_help=False,
            )
            parser.add_argument(
                "-v",
                "--value",
                dest="value",
                action="store",
                required=False,
                type=type_,  # type: ignore[arg-type]
                choices=choices,
            )
            ns_parser, _ = self.parse_simple_args(parser, other_args)
            if ns_parser:
                if ns_parser.value:
                    # Console style is applied immediately
                    if command == "console_style":
                        session.style.apply(ns_parser.value)
                    session.settings.set_item(field_name, ns_parser.value)
                    session.console.print(
                        f"[info]Current value:[/info] {getattr(session.settings, field_name)}"
                    )
                elif not other_args:
                    session.console.print(
                        f"[info]Current value:[/info] {getattr(session.settings, field_name)}"
                    )