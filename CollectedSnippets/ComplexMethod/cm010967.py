def __init__(
        self,
        batch_shape: torch.Size = torch.Size(),
        event_shape: torch.Size = torch.Size(),
        validate_args: bool | None = None,
    ) -> None:
        self._batch_shape = batch_shape
        self._event_shape = event_shape
        if validate_args is not None:
            self._validate_args = validate_args
        if self._validate_args:
            try:
                arg_constraints = self.arg_constraints
            except NotImplementedError:
                arg_constraints = {}
                warnings.warn(
                    f"{self.__class__} does not define `arg_constraints`. "
                    + "Please set `arg_constraints = {}` or initialize the distribution "
                    + "with `validate_args=False` to turn off validation.",
                    stacklevel=2,
                )
            for param, constraint in arg_constraints.items():
                if constraints.is_dependent(constraint):
                    continue  # skip constraints that cannot be checked
                if param not in self.__dict__ and isinstance(
                    getattr(type(self), param), lazy_property
                ):
                    continue  # skip checking lazily-constructed args
                value = getattr(self, param)
                valid = constraint.check(value)
                if not torch._is_all_true(valid):
                    raise ValueError(
                        f"Expected parameter {param} "
                        f"({type(value).__name__} of shape {tuple(value.shape)}) "
                        f"of distribution {repr(self)} "
                        f"to satisfy the constraint {repr(constraint)}, "
                        f"but found invalid values:\n{value}"
                    )
        super().__init__()