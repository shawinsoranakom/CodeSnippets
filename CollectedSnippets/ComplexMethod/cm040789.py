def _evaluate_condition(self, value, condition, field_exists: bool):
        if not isinstance(condition, dict):
            return field_exists and value == condition
        elif (must_exist := condition.get("exists")) is not None:
            # if must_exists is True then field_exists must be True
            # if must_exists is False then fields_exists must be False
            return must_exist == field_exists
        elif value is None:
            # the remaining conditions require the value to not be None
            return False
        elif anything_but := condition.get("anything-but"):
            if isinstance(anything_but, dict):
                not_prefix = anything_but.get("prefix")
                return not value.startswith(not_prefix)
            elif isinstance(anything_but, list):
                return value not in anything_but
            else:
                return value != anything_but
        elif prefix := condition.get("prefix"):
            return value.startswith(prefix)
        elif suffix := condition.get("suffix"):
            return value.endswith(suffix)
        elif equal_ignore_case := condition.get("equals-ignore-case"):
            return equal_ignore_case.lower() == value.lower()
        elif numeric_condition := condition.get("numeric"):
            return self._evaluate_numeric_condition(numeric_condition, value)
        elif cidr := condition.get("cidr"):
            try:
                ip = ipaddress.ip_address(value)
                return ip in ipaddress.ip_network(cidr)
            except ValueError:
                return False

        return False