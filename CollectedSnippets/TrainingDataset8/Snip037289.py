def value(self) -> Any:
        """Get the value of this config option."""
        if self._get_val_func is None:
            return None
        return self._get_val_func()