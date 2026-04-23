def __init__(
        self,
        name,
        *,
        # The identity value for the operator if it has one.
        identity: Any | None = None,
        # The nan policy for the operator if it implements one.
        # - propagate: NaN values are propagated to the output
        # - omit: NaN values are discarded during the reduction
        nan_policy: str | None = None,
        # Whether the operator supports reducing multiple dimensions.
        supports_multiple_dims: bool = True,
        # Whether the operator promotes integral to floating point dtypes.
        promotes_int_to_float: bool = False,
        # Whether the operator promotes all integral dtypes to int64.
        promotes_int_to_int64: bool = False,
        # If a specific dtype is given, then the operator always returns that
        # dtype irrespective of the input dtype. If None, the operator returns
        # the dtype according to the type promotion rules above.
        result_dtype: torch.dtype | None = None,
        # Casts complex results to real (e.g. linalg.norm or torch.var)
        complex_to_real: bool = False,
        # ReductionOpInfo tests generate their own input, dim and keepdim
        # arguments and call this function to generate tuples of extra args and
        # kwargs to use when calling the op. This is required for operators that
        # have other required parameters besides the input tensor.
        generate_args_kwargs: Callable = lambda t, dim=None, keepdim=False: (
            yield (
                (),
                {},
            )
        ),
        # Options from the OpInfo base class
        **kwargs,
    ):
        self._original_reduction_args = locals().copy()
        if nan_policy not in (None, "propagate", "omit"):
            raise AssertionError(
                f"nan_policy must be None, 'propagate', or 'omit', got {nan_policy}"
            )

        # These are mutually exclusive options
        if result_dtype and promotes_int_to_float:
            raise AssertionError(
                "result_dtype and promotes_int_to_float are mutually exclusive"
            )
        if result_dtype and promotes_int_to_int64:
            raise AssertionError(
                "result_dtype and promotes_int_to_int64 are mutually exclusive"
            )
        if result_dtype and complex_to_real:
            raise AssertionError(
                "result_dtype and complex_to_real are mutually exclusive"
            )
        if promotes_int_to_float and promotes_int_to_int64:
            raise AssertionError(
                "promotes_int_to_float and promotes_int_to_int64 are mutually exclusive"
            )

        # Default sample_inputs_func for ReductionOpInfo which augments sample
        # inputs from sample_inputs_reduction with the args and kwargs from
        # generate_args_kwargs. This is only used if sample_inputs_func is None.
        def sample_inputs_func(*args, **kwargs):
            kwargs["supports_multiple_dims"] = supports_multiple_dims
            kwargs["generate_args_kwargs"] = generate_args_kwargs
            yield from sample_inputs_reduction(*args, **kwargs)

        # Override OpInfo defaults and call base class __init__
        kwargs.setdefault("inplace_variant", None)
        kwargs.setdefault("sample_inputs_func", sample_inputs_func)
        super().__init__(name, promotes_int_to_float=promotes_int_to_float, **kwargs)

        self.identity = identity
        self.nan_policy = nan_policy
        self.supports_multiple_dims = supports_multiple_dims
        self.promotes_int_to_int64 = promotes_int_to_int64
        self.complex_to_real = complex_to_real
        self.result_dtype = result_dtype
        self.generate_args_kwargs = generate_args_kwargs