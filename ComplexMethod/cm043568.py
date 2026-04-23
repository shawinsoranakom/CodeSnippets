def _build_custom_groups(self):
        """Build the custom groups from the reference."""
        for route, v in self._reference.items():
            for provider, args in v["parameters"].items():
                if provider == "standard":
                    continue

                custom_arguments = []
                for arg in args:
                    if arg.get("standard"):
                        continue

                    type_ = self._parse_type(arg["type"])

                    custom_arguments.append(
                        ArgparseArgumentModel(
                            name=arg["name"],
                            type=type_,
                            dest=arg["name"],
                            default=arg["default"],
                            required=not (arg["optional"]),
                            action="store" if type_ is not bool else "store_true",
                            help=arg["description"],
                            nargs=self._get_nargs(type_),
                            choices=self._get_choices(
                                arg["type"], custom_choices=arg["choices"]
                            ),
                        )
                    )

                group = ArgparseArgumentGroupModel(
                    name=provider, arguments=custom_arguments
                )

                if route not in self._custom_groups:
                    self._custom_groups[route] = []

                self._custom_groups[route].append(group)