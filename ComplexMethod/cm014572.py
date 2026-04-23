def __post_init__(self) -> None:
        test_sig: FunctionSchema = self.functional.func.signature()
        for f in self.functions():
            if test_sig != f.func.signature():
                raise AssertionError(
                    "NativeFunctionsGroup constructed from two NativeFunctions "
                    f"that don't have matching signatures: {test_sig} != {f.func.signature()}"
                )

            if self.structured != f.part_of_structured_group:
                raise AssertionError(
                    "NativeFunctionsGroup constructed from structured and unstructured "
                    f"functions: {self.out.func.name} and {f.func.name}"
                )
        if self.functional.func.kind() != SchemaKind.functional:
            raise AssertionError(
                f"functional.func.kind() is {self.functional.func.kind()}, expected SchemaKind.functional"
            )
        if self.out.func.kind() != SchemaKind.out:
            raise AssertionError(
                f"out.func.kind() is {self.out.func.kind()}, expected SchemaKind.out"
            )
        if self.functional.namespace != self.out.namespace:
            raise AssertionError(
                f"functional.namespace ({self.functional.namespace}) != out.namespace ({self.out.namespace})"
            )
        if self.inplace is not None:
            if self.inplace.func.kind() != SchemaKind.inplace:
                raise AssertionError(
                    f"inplace.func.kind() is {self.inplace.func.kind()}, expected SchemaKind.inplace"
                )
            if self.inplace.namespace != self.functional.namespace:
                raise AssertionError(
                    f"inplace.namespace ({self.inplace.namespace}) != functional.namespace ({self.functional.namespace})"
                )

        if self.mutable is not None:
            if self.mutable.func.kind() != SchemaKind.mutable:
                raise AssertionError(
                    f"mutable.func.kind() is {self.mutable.func.kind()}, expected SchemaKind.mutable"
                )
            if self.mutable.namespace != self.functional.namespace:
                raise AssertionError(
                    f"mutable.namespace ({self.mutable.namespace}) != functional.namespace ({self.functional.namespace})"
                )
            # See Note [Overload Ambiguity With Functional Variants]
            if not self.functional.func.name.name.functional_overload:
                raise AssertionError(
                    "functional.func.name.name.functional_overload must be True when mutable is not None"
                )

        if self.structured:
            # For now, structured composite kernels are not supported (need some
            # design work to figure out how to make the composite case work)
            if (
                self.out.has_composite_implicit_autograd_kernel
                or self.out.has_composite_implicit_autograd_nested_tensor_kernel
            ):
                raise AssertionError("structured composite kernels are not supported")

            if self.functional.structured_delegate != self.out.func.name:
                raise AssertionError(
                    f"{self.functional.func.name} delegates to {self.functional.structured_delegate} "
                    f"but its actual delegate is {self.out.func.name}"
                )
            if self.inplace is not None:
                if self.inplace.structured_delegate != self.out.func.name:
                    raise AssertionError(
                        f"{self.inplace.func.name} delegates to {self.inplace.structured_delegate} "
                        f"but its actual delegate is {self.out.func.name}"
                    )

        generated_fns = sorted(
            [str(f.func.name) for f in self.functions() if "generated" in f.tags]
        )
        generated_fns_str = ", ".join(str(x) for x in generated_fns)
        expected_generated_fns: set[str] = set()
        for f in self.functions():
            expected_generated_fns.update(str(op) for op in f.autogen)
        expected_generated_fns_str = ", ".join(
            str(x) for x in sorted(expected_generated_fns)
        )
        if len(expected_generated_fns) == 0 and len(generated_fns) > 0:
            raise RuntimeError(
                f"The codegen expects to be able to generate '{generated_fns_str}'."
                " In order to generate them however, we expect them to be called out explicitly in the yaml."
                f" Please add an 'autogen: {generated_fns_str}' line to the entry for {str(f.func.name)}"
            )
        if expected_generated_fns_str != generated_fns_str:
            raise RuntimeError(
                f"The codegen expects to be able to generate '{generated_fns_str}'."
                f" To do so, it expects a line: 'autogen: {generated_fns_str}'."
                f" Instead, it found 'autogen: {expected_generated_fns_str}'"
            )