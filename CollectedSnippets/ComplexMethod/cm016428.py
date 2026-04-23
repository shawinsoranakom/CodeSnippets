def validate(self) -> None:
        if not isinstance(self.widgets, list) or any(not isinstance(x, str) for x in self.widgets):
            raise ValueError("PriceBadgeDepends.widgets must be a list[str].")
        if not isinstance(self.inputs, list) or any(not isinstance(x, str) for x in self.inputs):
            raise ValueError("PriceBadgeDepends.inputs must be a list[str].")
        if not isinstance(self.input_groups, list) or any(not isinstance(x, str) for x in self.input_groups):
            raise ValueError("PriceBadgeDepends.input_groups must be a list[str].")