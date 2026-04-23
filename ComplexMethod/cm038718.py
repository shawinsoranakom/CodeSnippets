def _update_nested(
        self,
        target: PretrainedConfig | dict[str, Any],
        updates: dict[str, Any],
    ) -> None:
        """Recursively updates a config or dict with nested updates."""
        for key, value in updates.items():
            if isinstance(value, dict):
                # Get the nested target
                if isinstance(target, dict):
                    nested_target = target.get(key)
                else:
                    nested_target = getattr(target, key, None)

                # If nested target exists and can be updated recursively
                if nested_target is not None and (
                    isinstance(nested_target, dict)
                    or hasattr(nested_target, "__dict__")
                ):
                    self._update_nested(nested_target, value)
                    continue

            # Set the value (base case)
            if isinstance(target, dict):
                target[key] = value
            else:
                setattr(target, key, value)