def _validate_rule(self, rule: t.Any, from_: str | None = None) -> None:
        match rule:
            case None | str() | bool():
                return

            case int() | float():
                # TODO: AWS says they support only from -10^9 to 10^9 but seems to accept it, so we just return
                # if rule <= -1000000000 or rule >= 1000000000:
                #     raise ""
                return

            case {**kwargs}:
                if len(kwargs) != 1:
                    raise InvalidEventPatternException(
                        f"{self.error_prefix}Only one key allowed in match expression"
                    )

                operator, value = None, None
                for k, v in kwargs.items():
                    operator, value = k, v

                if operator in (
                    "prefix",
                    "suffix",
                ):
                    if from_ == "anything-but":
                        if isinstance(value, dict):
                            raise InvalidEventPatternException(
                                f"{self.error_prefix}Value of {from_} must be an array or single string/number value."
                            )

                        if not self._is_str_or_list_of_str(value):
                            raise InvalidEventPatternException(
                                f"{self.error_prefix}prefix/suffix match pattern must be a string"
                            )
                        elif not value:
                            raise InvalidEventPatternException(
                                f"{self.error_prefix}Null prefix/suffix not allowed"
                            )

                    elif isinstance(value, dict):
                        for inner_operator in value.keys():
                            if inner_operator != "equals-ignore-case":
                                raise InvalidEventPatternException(
                                    f"{self.error_prefix}Unsupported anything-but pattern: {inner_operator}"
                                )

                    elif not isinstance(value, str):
                        raise InvalidEventPatternException(
                            f"{self.error_prefix}{operator} match pattern must be a string"
                        )
                    return

                elif operator == "equals-ignore-case":
                    if from_ == "anything-but":
                        if not self._is_str_or_list_of_str(value):
                            raise InvalidEventPatternException(
                                f"{self.error_prefix}Inside {from_}/{operator} list, number|start|null|boolean is not supported."
                            )
                    elif not isinstance(value, str):
                        raise InvalidEventPatternException(
                            f"{self.error_prefix}{operator} match pattern must be a string"
                        )
                    return

                elif operator == "anything-but":
                    # anything-but can actually contain any kind of simple rule (str, number, and list) except Null
                    if value is None:
                        raise InvalidEventPatternException(
                            f"{self.error_prefix}Value of anything-but must be an array or single string/number value."
                        )
                    if isinstance(value, list):
                        for v in value:
                            if v is None:
                                raise InvalidEventPatternException(
                                    f"{self.error_prefix}Inside anything but list, start|null|boolean is not supported."
                                )
                            self._validate_rule(v, from_="anything-but")

                        return

                    # or have a nested `prefix`, `suffix` or `equals-ignore-case` pattern
                    elif isinstance(value, dict):
                        for inner_operator in value.keys():
                            if inner_operator not in (
                                "prefix",
                                "equals-ignore-case",
                                "suffix",
                                "wildcard",
                            ):
                                raise InvalidEventPatternException(
                                    f"{self.error_prefix}Unsupported anything-but pattern: {inner_operator}"
                                )

                    self._validate_rule(value, from_="anything-but")
                    return

                elif operator == "exists":
                    if not isinstance(value, bool):
                        raise InvalidEventPatternException(
                            f"{self.error_prefix}exists match pattern must be either true or false."
                        )
                    return

                elif operator == "numeric":
                    self._validate_numeric_condition(value)

                elif operator == "cidr":
                    self._validate_cidr_condition(value)

                elif operator == "wildcard":
                    if from_ == "anything-but" and isinstance(value, list):
                        for v in value:
                            self._validate_wildcard(v)
                    else:
                        self._validate_wildcard(value)

                else:
                    raise InvalidEventPatternException(
                        f"{self.error_prefix}Unrecognized match type {operator}"
                    )

            case _:
                raise InvalidEventPatternException(
                    f"{self.error_prefix}Match value must be String, number, true, false, or null"
                )