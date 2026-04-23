def _inner(
            policy_elements: dict[str, t.Any], depth: int = 1, combinations: int = 1
        ) -> tuple[list[list[t.Any]], int]:
            _rules = []
            for key, _value in policy_elements.items():
                if isinstance(_value, dict):
                    # From AWS docs: "unlike attribute-based policies, payload-based policies support property nesting."
                    sub_rules, combinations = _inner(
                        _value, depth=depth + 1, combinations=combinations
                    )
                    _rules.extend(sub_rules)
                elif isinstance(_value, list):
                    if not _value:
                        raise InvalidParameterException(
                            f"{self.error_prefix}FilterPolicy: Empty arrays are not allowed"
                        )

                    current_combination = 0
                    if key == "$or":
                        for val in _value:
                            sub_rules, or_combinations = _inner(
                                val, depth=depth, combinations=combinations
                            )
                            _rules.extend(sub_rules)
                            current_combination += or_combinations

                        combinations = current_combination
                    else:
                        _rules.append(_value)
                        combinations = combinations * len(_value) * depth
                else:
                    raise InvalidParameterException(
                        f'{self.error_prefix}FilterPolicy: "{key}" must be an object or an array'
                    )

            if self.scope == "MessageAttributes" and depth > 1:
                raise InvalidParameterException(
                    f"{self.error_prefix}Filter policy scope MessageAttributes does not support nested filter policy"
                )

            return _rules, combinations