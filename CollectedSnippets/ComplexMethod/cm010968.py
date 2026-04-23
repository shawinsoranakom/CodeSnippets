def _validate_sample(self, value: Tensor) -> None:
        """
        Argument validation for distribution methods such as `log_prob`,
        `cdf` and `icdf`. The rightmost dimensions of a value to be
        scored via these methods must agree with the distribution's batch
        and event shapes.

        Args:
            value (Tensor): the tensor whose log probability is to be
                computed by the `log_prob` method.
        Raises
            ValueError: when the rightmost dimensions of `value` do not match the
                distribution's batch and event shapes.
        """
        if not isinstance(value, torch.Tensor):
            raise ValueError("The value argument to log_prob must be a Tensor")

        event_dim_start = len(value.size()) - len(self._event_shape)
        if value.size()[event_dim_start:] != self._event_shape:
            raise ValueError(
                f"The right-most size of value must match event_shape: {value.size()} vs {self._event_shape}."
            )

        actual_shape = value.size()
        expected_shape = self._batch_shape + self._event_shape
        for i, j in zip(reversed(actual_shape), reversed(expected_shape)):
            if i != 1 and j != 1 and i != j:
                raise ValueError(
                    f"Value is not broadcastable with batch_shape+event_shape: {actual_shape} vs {expected_shape}."
                )
        try:
            support = self.support
        except NotImplementedError:
            warnings.warn(
                f"{self.__class__} does not define `support` to enable "
                + "sample validation. Please initialize the distribution with "
                + "`validate_args=False` to turn off validation.",
                stacklevel=2,
            )
            return
        if support is None:
            raise AssertionError("support is unexpectedly None")
        valid = support.check(value)
        if not torch._is_all_true(valid):
            raise ValueError(
                "Expected value argument "
                f"({type(value).__name__} of shape {tuple(value.shape)}) "
                f"to be within the support ({repr(support)}) "
                f"of the distribution {repr(self)}, "
                f"but found invalid values:\n{value}"
            )