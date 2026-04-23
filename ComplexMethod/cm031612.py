def _check_args_match(self, name: str, args: list[str]) -> None:
        current_args = self.events[name]
        msg = (
            f"Mismatched arguments for audit-event {name}: "
            f"{current_args!r} != {args!r}"
        )
        if current_args == args:
            return
        if len(current_args) != len(args):
            logger.warning(msg)
            return
        for a1, a2 in zip(current_args, args, strict=False):
            if a1 == a2:
                continue
            if any(a1 in s and a2 in s for s in _SYNONYMS):
                continue
            logger.warning(msg)
            return