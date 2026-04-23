def _handle_argument_in_groups(self, argument, group):
        """Handle the argument and add it to the parser."""

        def _update_providers(input_string: str, new_provider: list[str | None]) -> str:
            pattern = r"\(provider:\s*(.*?)\)"
            providers = re.findall(pattern, input_string)
            providers.extend(new_provider)
            # remove pattern from help and add with new providers
            input_string = re.sub(pattern, "", input_string).strip()
            return f"{input_string} (provider: {', '.join(providers)})"

        # check if the argument is already in use, if not, add it
        if f"--{argument.name}" not in self._parser._option_string_actions:
            kwargs = argument.model_dump(exclude={"name"}, exclude_none=True)
            if "help" in kwargs:
                kwargs["help"] = ArgparseTranslator._escape_help(kwargs["help"])
            group.add_argument(f"--{argument.name}", **kwargs)
            if group.title in self.provider_parameters:
                self.provider_parameters[group.title].append(argument.name)

        else:
            kwargs = argument.model_dump(exclude={"name"}, exclude_none=True)
            model_choices = kwargs.get("choices", ()) or ()
            # extend choices
            existing_choices = get_argument_choices(self._parser, argument.name)
            choices = tuple(set(existing_choices + model_choices))
            optional_choices = bool(existing_choices and not model_choices)

            # check if the argument is in the required arguments
            if in_group(self._parser, argument.name, group_title="required arguments"):
                for action in self._required._group_actions:
                    if action.dest == argument.name and choices:
                        # update choices
                        action.choices = choices
                        set_optional_choices(action, optional_choices)
                return

            # check if the argument is in the optional arguments
            if in_group(self._parser, argument.name, group_title="optional arguments"):
                for action in self._parser._actions:
                    if action.dest == argument.name:
                        # update choices
                        if choices:
                            action.choices = choices
                            set_optional_choices(action, optional_choices)
                        if argument.name not in self.signature.parameters:
                            # update help
                            action.help = ArgparseTranslator._escape_help(
                                _update_providers(action.help or "", [group.title])
                            )
                return

            # we need to check if the optional choices were set in other group
            # before we remove the argument from the group, otherwise we will lose info
            if not optional_choices:
                optional_choices = get_argument_optional_choices(
                    self._parser, argument.name
                )

            # if the argument is in use, remove it from all groups
            # and return the groups that had the argument
            groups_w_arg = remove_argument(self._parser, argument.name)
            groups_w_arg.append(group.title)  # add current group

            # add it to the optional arguments group instead
            if choices:
                kwargs["choices"] = choices  # update choices
            # add provider info to the help
            kwargs["help"] = ArgparseTranslator._escape_help(
                _update_providers(argument.help or "", groups_w_arg)
            )
            action = self._parser.add_argument(f"--{argument.name}", **kwargs)
            set_optional_choices(action, optional_choices)