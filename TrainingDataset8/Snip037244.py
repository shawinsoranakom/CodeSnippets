def __call__(
        self,
        *args,
        default: Any = None,
        key: Optional[str] = None,
        **kwargs,
    ) -> Any:
        """An alias for create_instance."""
        return self.create_instance(*args, default=default, key=key, **kwargs)