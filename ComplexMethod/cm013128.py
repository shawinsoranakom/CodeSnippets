def _equalize_attributes(
        self, actual: torch.Tensor, expected: torch.Tensor
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """Equalizes some attributes of two tensors for value comparison.

        If ``actual`` and ``expected`` are ...

        - ... not on the same :attr:`~torch.Tensor.device`, they are moved CPU memory.
        - ... not of the same ``dtype``, they are promoted  to a common ``dtype`` (according to
            :func:`torch.promote_types`).
        - ... not of the same ``layout``, they are converted to strided tensors.

        Args:
            actual (Tensor): Actual tensor.
            expected (Tensor): Expected tensor.

        Returns:
            (Tuple[Tensor, Tensor]): Equalized tensors.
        """
        # The comparison logic uses operators currently not supported by the MPS backends.
        #  See https://github.com/pytorch/pytorch/issues/77144 for details.
        # TODO: Remove this conversion as soon as all operations are supported natively by the MPS backend
        if actual.is_mps or expected.is_mps:  # type: ignore[attr-defined]
            actual = actual.cpu()
            expected = expected.cpu()

        if actual.device != expected.device:
            actual = actual.cpu()
            expected = expected.cpu()

        if actual.dtype != expected.dtype:
            actual_dtype = actual.dtype
            expected_dtype = expected.dtype
            # For uint64, this is not sound in general, which is why promote_types doesn't
            # allow it, but for easy testing, we're unlikely to get confused
            # by large uint64 overflowing into negative int64
            if actual_dtype in [torch.uint64, torch.uint32, torch.uint16]:
                actual_dtype = torch.int64
            if expected_dtype in [torch.uint64, torch.uint32, torch.uint16]:
                expected_dtype = torch.int64
            dtype = torch.promote_types(actual_dtype, expected_dtype)
            actual = actual.to(dtype)
            expected = expected.to(dtype)

        if actual.layout != expected.layout:
            # These checks are needed, since Tensor.to_dense() fails on tensors that are already strided
            actual = actual.to_dense() if actual.layout != torch.strided else actual
            expected = (
                expected.to_dense() if expected.layout != torch.strided else expected
            )

        return actual, expected