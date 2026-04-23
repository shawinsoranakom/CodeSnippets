def _parse(self, config_str: str) -> None:
        if not config_str or not config_str.strip():
            return

        rule_strs = config_str.split(";")
        for rule_str in rule_strs:
            rule_str = rule_str.strip()
            if not rule_str:
                continue

            colon_idx = rule_str.find(":")
            if colon_idx == -1:
                log.warning(
                    "Invalid %s override rule (missing ':'): %s",
                    self._rule_type,
                    rule_str,
                )
                continue

            filter_str = rule_str[:colon_idx].strip()
            value_str = rule_str[colon_idx + 1 :].strip()

            if not filter_str or not value_str:
                log.warning("Invalid %s override rule: %s", self._rule_type, rule_str)
                continue

            value = self._parse_value_str(value_str)
            if value is not None:
                self._rules.append((GraphIdFilter(filter_str), value))