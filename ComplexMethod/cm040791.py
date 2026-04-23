def _validate_rule(self, rule: t.Any) -> None:
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
                    raise InvalidParameterException(
                        f"{self.error_prefix}FilterPolicy: Only one key allowed in match expression"
                    )

                operator, value = None, None
                for k, v in kwargs.items():
                    operator, value = k, v

                if operator in (
                    "equals-ignore-case",
                    "prefix",
                    "suffix",
                ):
                    if not isinstance(value, str):
                        raise InvalidParameterException(
                            f"{self.error_prefix}FilterPolicy: {operator} match pattern must be a string"
                        )
                    return

                elif operator == "anything-but":
                    # anything-but can actually contain any kind of simple rule (str, number, and list)
                    if isinstance(value, list):
                        for v in value:
                            self._validate_rule(v)

                        return

                    # or have a nested `prefix` pattern
                    elif isinstance(value, dict):
                        for inner_operator in value.keys():
                            if inner_operator != "prefix":
                                raise InvalidParameterException(
                                    f"{self.error_prefix}FilterPolicy: Unsupported anything-but pattern: {inner_operator}"
                                )

                    self._validate_rule(value)
                    return

                elif operator == "exists":
                    if not isinstance(value, bool):
                        raise InvalidParameterException(
                            f"{self.error_prefix}FilterPolicy: exists match pattern must be either true or false."
                        )
                    return

                elif operator == "numeric":
                    self._validate_numeric_condition(value)

                elif operator == "cidr":
                    self._validate_cidr_condition(value)

                else:
                    raise InvalidParameterException(
                        f"{self.error_prefix}FilterPolicy: Unrecognized match type {operator}"
                    )

            case _:
                raise InvalidParameterException(
                    f"{self.error_prefix}FilterPolicy: Match value must be String, number, true, false, or null"
                )