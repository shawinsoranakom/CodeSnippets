def _check_choices(self):
        if not self.choices:
            return []

        if not isinstance(self.choices, Iterable) or isinstance(
            self.choices, (str, set, frozenset)
        ):
            return [
                checks.Error(
                    "'choices' must be a mapping (e.g. a dictionary) or an "
                    "ordered iterable (e.g. a list or tuple, but not a set).",
                    obj=self,
                    id="fields.E004",
                )
            ]

        choice_max_length = 0
        # Expect [group_name, [value, display]]
        for choices_group in self.choices:
            try:
                group_name, group_choices = choices_group
            except (TypeError, ValueError):
                # Containing non-pairs
                break
            try:
                if not all(
                    self._choices_is_value(value) and self._choices_is_value(human_name)
                    for value, human_name in group_choices
                ):
                    break
                if self.max_length is not None and group_choices:
                    choice_max_length = max(
                        [
                            choice_max_length,
                            *(
                                len(value)
                                for value, _ in group_choices
                                if isinstance(value, str)
                            ),
                        ]
                    )
            except (TypeError, ValueError):
                # No groups, choices in the form [value, display]
                value, human_name = group_name, group_choices
                if not self._choices_is_value(value) or not self._choices_is_value(
                    human_name
                ):
                    break
                if self.max_length is not None and isinstance(value, str):
                    choice_max_length = max(choice_max_length, len(value))

            # Special case: choices=['ab']
            if isinstance(choices_group, str):
                break
        else:
            if self.max_length is not None and choice_max_length > self.max_length:
                return [
                    checks.Error(
                        "'max_length' is too small to fit the longest value "
                        "in 'choices' (%d characters)." % choice_max_length,
                        obj=self,
                        id="fields.E009",
                    ),
                ]
            return []

        return [
            checks.Error(
                "'choices' must be a mapping of actual values to human readable names "
                "or an iterable containing (actual value, human readable name) tuples.",
                obj=self,
                id="fields.E005",
            )
        ]