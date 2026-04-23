def param_allowed(
        self, stat_name: str, include: Sequence[str], exclude: Sequence[str]
    ) -> bool:
        if not include and not exclude:
            return True
        for p in exclude:
            if p in stat_name:
                return False
        if exclude and not include:
            return True
        return any(p in stat_name for p in include)