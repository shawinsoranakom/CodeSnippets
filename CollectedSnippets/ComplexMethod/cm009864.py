def _check_evaluation_args(
        self,
        reference: str | None = None,
        input_: str | None = None,
    ) -> None:
        """Check if the evaluation arguments are valid.

        Args:
            reference: The reference label.
            input_: The input string.

        Raises:
            ValueError: If the evaluator requires an input string but none is provided,
                or if the evaluator requires a reference label but none is provided.
        """
        if self.requires_input and input_ is None:
            msg = f"{self.__class__.__name__} requires an input string."
            raise ValueError(msg)
        if input_ is not None and not self.requires_input:
            warn(self._skip_input_warning, stacklevel=3)
        if self.requires_reference and reference is None:
            msg = f"{self.__class__.__name__} requires a reference string."
            raise ValueError(msg)
        if reference is not None and not self.requires_reference:
            warn(self._skip_reference_warning, stacklevel=3)