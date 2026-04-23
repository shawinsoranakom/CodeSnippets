def __init__(
        self,
        input,
        *var_args,
        args=None,
        kwargs=None,
        output_process_fn_grad=None,
        broadcasts_input=None,
        name=None,
        **var_kwargs,
    ):
        # input is the first input to the op and is typically either a Tensor or TensorList (Sequence[Tensor]).
        # This follows the typical pattern where for Tensor inputs op(t, ...) = t.op(...).
        self.input = input

        # Allow calling either as SampleInput(input, args=args, kwargs=kwargs), or as
        # SampleInput(input, *args, **kwargs) but not to mix the two forms
        if args is not None or kwargs is not None:
            if var_args or var_kwargs:
                raise AssertionError(
                    "A SampleInput can be constructed 'naturally' with *args and **kwargs or by "
                    "explicitly setting the 'args' and 'kwargs' parameters, but the two "
                    "methods of construction cannot be mixed!"
                )
        elif var_args or var_kwargs:
            if not (
                output_process_fn_grad is None
                and broadcasts_input is None
                and name is None
            ):
                raise AssertionError(
                    "A SampleInput constructed 'naturally' with *args and **kwargs "
                    "cannot specify additional metadata in keyword arguments"
                )

        self.args = args if args is not None else var_args
        if not isinstance(self.args, tuple):
            raise AssertionError(f"Expected args to be tuple, got {type(self.args)}")
        self.kwargs = kwargs if kwargs is not None else var_kwargs
        if not isinstance(self.kwargs, dict):
            raise AssertionError(f"Expected kwargs to be dict, got {type(self.kwargs)}")

        self.output_process_fn_grad = (
            output_process_fn_grad
            if output_process_fn_grad is not None
            else lambda x: x
        )
        self.name = name if name is not None else ""

        # Specifies if `self.input` is broadcasted or not,
        # given that the operator supports broadcasting.
        # This field is used to verify the behavior for inplace variant.
        #
        # If a SampleInput is marked with `broadcasts_input=True`,
        # it is verified that we get a `RuntimeError` with this sample,
        # and inplace variant. Also inplace grad{grad} tests are skipped,
        # for such inputs (as they will error out otherwise).
        self.broadcasts_input = (
            broadcasts_input if broadcasts_input is not None else False
        )