def _evaluate_condition(self, value: t.Any, condition: t.Any, field_exists: bool) -> bool:
        if not isinstance(condition, dict):
            return field_exists and value == condition

        elif (must_exist := condition.get("exists")) is not None:
            # if must_exists is True then field_exists must be True
            # if must_exists is False then fields_exists must be False
            return must_exist == field_exists

        elif (anything_but := condition.get("anything-but")) is not None:
            if not field_exists:
                # anything-but can handle None `value`, but it needs to differentiate between user-set `null` and
                # missing value
                return False

            if isinstance(anything_but, dict):
                if (not_condition := anything_but.get("prefix")) is not None:
                    predicate = self._evaluate_prefix
                elif (not_condition := anything_but.get("suffix")) is not None:
                    predicate = self._evaluate_suffix
                elif (not_condition := anything_but.get("equals-ignore-case")) is not None:
                    predicate = self._evaluate_equal_ignore_case
                elif (not_condition := anything_but.get("wildcard")) is not None:
                    predicate = self._evaluate_wildcard
                else:
                    # this should not happen as we validate the EventPattern before
                    return False

                if isinstance(not_condition, str):
                    return not predicate(not_condition, value)
                elif isinstance(not_condition, list):
                    return all(
                        not predicate(sub_condition, value) for sub_condition in not_condition
                    )

            elif isinstance(anything_but, list):
                return value not in anything_but
            else:
                return value != anything_but

        elif value is None:
            # the remaining conditions require the value to not be None
            return False

        elif (prefix := condition.get("prefix")) is not None:
            if isinstance(prefix, dict):
                if (prefix_equal_ignore_case := prefix.get("equals-ignore-case")) is not None:
                    return self._evaluate_prefix(prefix_equal_ignore_case.lower(), value.lower())
            else:
                return self._evaluate_prefix(prefix, value)

        elif (suffix := condition.get("suffix")) is not None:
            if isinstance(suffix, dict):
                if (suffix_equal_ignore_case := suffix.get("equals-ignore-case")) is not None:
                    return self._evaluate_suffix(suffix_equal_ignore_case.lower(), value.lower())
            else:
                return self._evaluate_suffix(suffix, value)

        elif (equal_ignore_case := condition.get("equals-ignore-case")) is not None:
            return self._evaluate_equal_ignore_case(equal_ignore_case, value)

        # we validated that `numeric`  should be a non-empty list when creating the rule, we don't need the None check
        elif numeric_condition := condition.get("numeric"):
            return self._evaluate_numeric_condition(numeric_condition, value)

        # we also validated the `cidr` that it cannot be empty
        elif cidr := condition.get("cidr"):
            return self._evaluate_cidr(cidr, value)

        elif (wildcard := condition.get("wildcard")) is not None:
            return self._evaluate_wildcard(wildcard, value)

        return False