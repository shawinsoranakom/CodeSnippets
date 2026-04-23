def assertEqual(
            self,
            x,
            y,
            msg: str | Callable[[str], str] | None = None,
            *,
            atol: float | None = None,
            rtol: float | None = None,
            equal_nan=True,
            exact_dtype=True,
            # TODO: default this to True
            exact_device=False,
            exact_layout=False,
            exact_stride=False,
            exact_is_coalesced=False
    ):
        # Hide this function from `pytest`'s traceback
        __tracebackhide__ = True

        # numpy's dtypes are a superset of what PyTorch supports. In case we encounter an unsupported dtype, we fall
        # back to an elementwise comparison. Note that this has to happen here and not for example in
        # `TensorOrArrayPair`, since at that stage we can no longer split the array into its elements and perform
        # multiple comparisons.
        if any(
            isinstance(input, np.ndarray) and not has_corresponding_torch_dtype(input.dtype) for input in (x, y)
        ):
            def to_list(input):
                return input.tolist() if isinstance(input, (torch.Tensor, np.ndarray)) else list(input)

            x = to_list(x)
            y = to_list(y)
        # When comparing a sequence of numbers to a tensor, we need to convert the sequence to a tensor here.
        # Otherwise, the pair origination of `are_equal` will fail, because the sequence is recognized as container
        # that should be checked elementwise while the tensor is not.
        elif isinstance(x, torch.Tensor) and isinstance(y, Sequence):
            y = torch.as_tensor(y, dtype=x.dtype, device=x.device)
        elif isinstance(x, Sequence) and isinstance(y, torch.Tensor):
            x = torch.as_tensor(x, dtype=y.dtype, device=y.device)

        # unbind NSTs to compare them; don't do this for NJTs
        if isinstance(x, torch.Tensor) and x.is_nested and x.layout == torch.strided:
            x = x.unbind()
        if isinstance(y, torch.Tensor) and y.is_nested and y.layout == torch.strided:
            y = y.unbind()

        x, y = _unwrap_dtensor_for_comparison(x, y)

        error_metas = not_close_error_metas(
            x,
            y,
            pair_types=(
                NonePair,
                RelaxedBooleanPair,
                RelaxedNumberPair,
                TensorOrArrayPair,
                TypedStoragePair,
                StringPair,
                SetPair,
                TypePair,
                ObjectPair,
            ),
            sequence_types=(
                Sequence,
                Sequential,
                ModuleList,
                ParameterList,
                ScriptList,
                torch.utils.data.dataset.Subset,
            ),
            mapping_types=(Mapping, ModuleDict, ParameterDict, ScriptDict),
            rtol=rtol,
            rtol_override=self.rel_tol,
            atol=atol,
            atol_override=self.precision,
            equal_nan=equal_nan,
            check_device=exact_device,
            check_dtype=exact_dtype,
            check_layout=exact_layout,
            check_stride=exact_stride,
            check_is_coalesced=exact_is_coalesced,
        )

        if error_metas:
            # See [ErrorMeta Cycles]
            error_metas = [error_metas]  # type: ignore[list-item]
            # TODO: compose all metas into one AssertionError
            raise error_metas.pop()[0].to_error(  # type: ignore[index]
                # This emulates unittest.TestCase's behavior if a custom message passed and
                # TestCase.longMessage (https://docs.python.org/3/library/unittest.html#unittest.TestCase.longMessage)
                # is True (default)
                (lambda generated_msg: f"{generated_msg}\n{msg}") if isinstance(msg, str) and self.longMessage else msg
            )