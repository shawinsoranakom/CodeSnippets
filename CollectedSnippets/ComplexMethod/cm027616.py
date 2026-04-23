def has_constraints(self) -> bool:
        """Returns True if at least one constraint is set (ignores assistant)."""
        return bool(
            self.name
            or self.area_name
            or self.floor_name
            or self.domains
            or self.device_classes
            or self.features
            or self.states
            or self.single_target
        )