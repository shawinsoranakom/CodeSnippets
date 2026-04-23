def __post_init__(self) -> None:
        # TODO: These invariants are weirdly asymmetric?
        # TODO: Fancier types?
        if self.self_arg is None:
            if self.pre_self_positional:
                raise AssertionError(
                    "pre_self_positional is non-empty but self_arg is None"
                )
        if self.tensor_options is None:
            if self.post_tensor_options_kwarg_only:
                raise AssertionError(
                    "post_tensor_options_kwarg_only is non-empty but tensor_options is None"
                )

        # We don't allow any of the following to have argument annotations,
        # to keep things simple.
        mutable_pre_self_positionals = [
            a
            for a in self.pre_self_positional
            if a.annotation is not None and a.annotation.is_write
        ]
        if len(mutable_pre_self_positionals) != 0:
            raise AssertionError(
                f"mutable pre_self_positional arguments are not currently supported in the schema: {mutable_pre_self_positionals}"
            )