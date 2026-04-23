def __init__(
        self,
        *,
        input_layouts: Placement | tuple[Placement | None, ...] | None = None,
        desired_input_layouts: Placement | tuple[Placement | None, ...] | None = None,
        input_kwarg_layouts: dict[str, Placement] | None = None,
        desired_input_kwarg_layouts: dict[str, Placement] | None = None,
        use_local_output: bool = False,
    ):
        self.input_layouts = (
            (input_layouts,) if isinstance(input_layouts, Placement) else input_layouts
        )
        self.desired_input_layouts = (
            (desired_input_layouts,)
            if isinstance(desired_input_layouts, Placement)
            else desired_input_layouts
        )
        self.use_local_output = use_local_output
        if self.input_layouts is not None:
            if self.desired_input_layouts is None:
                raise AssertionError("desired module inputs should not be None!")
            if len(self.input_layouts) != len(self.desired_input_layouts):
                raise AssertionError(
                    "input_layouts and desired_input_layouts should have same length!"
                )
        self.with_kwargs = input_kwarg_layouts is not None
        self.input_kwarg_layouts = input_kwarg_layouts or {}
        self.desired_input_kwarg_layouts = desired_input_kwarg_layouts or {}
        if self.with_kwargs:
            if len(self.input_kwarg_layouts) != len(self.desired_input_kwarg_layouts):
                raise AssertionError(
                    "input_kwarg_layouts and desired_input_kwarg_layouts should have same length!"
                )