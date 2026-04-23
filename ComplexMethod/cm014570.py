def __post_init__(self) -> None:
        if self.func.arguments.out:
            if self.variants != {Variant.function}:
                raise AssertionError(
                    "Native functions with out arguments MUST "
                    "be declared with only function variant; e.g., variants: function; "
                    "otherwise you will tickle a Python argument binding bug "
                    "(which usually manifests itself as the result variable being undefined.)"
                )
        if self.structured:
            if self.func.kind() != SchemaKind.out:
                raise AssertionError(
                    "Put structured field on the out= "
                    "variant of a function; did you mean structured_delegate?"
                )
            if not self.device_guard:
                raise AssertionError(
                    "device_guard: False is not respected by structured kernels"
                )
        if self.structured_delegate:
            if self.func.kind() == SchemaKind.out:
                raise AssertionError(
                    "structured_delegate field not allowed "
                    "on out= functions; did you mean structured?"
                )
            if not self.device_guard:
                raise AssertionError(
                    "device_guard: False is not respected by structured kernels"
                )
        # Technically, with the asserts above, this assert is impossible to
        # happen
        if self.structured and self.structured_delegate:
            raise AssertionError(
                "Cannot have both structured and structured_delegate on function"
            )
        defaulted_arguments = {
            a.name for a in self.func.schema_order_arguments() if a.default is not None
        }
        invalid_args = set.difference(self.cpp_no_default_args, defaulted_arguments)
        if len(invalid_args) != 0:
            raise AssertionError(f"Invalid cpp_no_default_args: {invalid_args}")
        if self.structured_inherits is not None:
            if not self.structured:
                raise AssertionError(
                    "structured_inherits must also imply structured: True"
                )
        if str(self.func.name).startswith("_foreach"):
            if self.device_check != DeviceCheckType.NoCheck:
                raise AssertionError(
                    "foreach kernels fall back to slow path when tensor are on different devices, "
                    "device_check not allowed to be enabled"
                )

        # NB: if your function accidentally has rand/dropout/... in its name
        # but is not actually random, feel free to amend this to special case
        if (
            "rand" in str(self.func.name)
            or (
                (
                    "dropout" in str(self.func.name)
                    or any(
                        "dropout" in arg.name for arg in self.func.arguments.flat_all
                    )
                )
                # Backwards of dropout is typically deterministic
                and "backward" not in str(self.func.name)
                and str(self.func.name.name) != "_cudnn_init_dropout_state"
            )
            or self.func.arguments.has_generator_arg()
        ):
            if "nondeterministic_seeded" not in self.tags:
                raise AssertionError(
                    f"nondeterministic_seeded tag missing for {self.func.name}"
                )