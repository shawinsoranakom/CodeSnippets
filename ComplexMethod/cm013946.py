def _parse(self, filter_str: str) -> None:
        if not filter_str or not filter_str.strip():
            return

        explicit_ids: set[int] = set()
        conditions: list[tuple[str, int]] = []

        # Pattern for comparison operators (>=, >, <=, <) followed by a number
        cmp_pattern = re.compile(r"^(>=|>|<=|<)(\d+)$")
        # Pattern for ranges like "10-20"
        range_pattern = re.compile(r"^(\d+)-(\d+)$")

        for part in filter_str.split(","):
            part = part.strip()
            if not part:
                continue

            if match := cmp_pattern.match(part):
                conditions.append((match.group(1), int(match.group(2))))
            elif match := range_pattern.match(part):
                start, end = int(match.group(1)), int(match.group(2))
                explicit_ids.update(range(start, end + 1))
            else:
                try:
                    explicit_ids.add(int(part))
                except ValueError:
                    log.warning("Invalid graph ID filter: %s", part)

        self._explicit_ids = frozenset(explicit_ids)
        self._conditions = conditions