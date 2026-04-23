def __post_init__(self) -> None:
        for arg, ret in zip(self.arguments.out, self.returns):
            if arg.annotation != ret.annotation:
                raise AssertionError(
                    "Out arguments must have matching return Tensor; furthermore, "
                    f"the ith-argument needs to correspond to the ith return. "
                    f"arg.annotation={arg.annotation}, ret.annotation={ret.annotation}"
                )
        # We also enforce that if you have any mutable, positional args, then they are not returned.
        # This makes it easier to group these functions properly with their functional/out= counterparts.
        for a in self.arguments.post_self_positional_mutable:
            if any(a.annotation == r.annotation for r in self.returns):
                raise AssertionError(
                    f"If you have a schema with mutable positional args, we expect them to not be returned. schema: {str(self)}"
                )
        # Invariant: we expect out arguments to appear as keyword arguments in the schema.
        # This means that all mutable returns should be aliased to a keyword argument
        # (except for "self", which we explicitly don't treat as an out argument because of its use in methods)
        # See Note [is_out_fn]
        out_and_self = list(self.arguments.out) + [
            arg for arg in self.arguments.flat_positional if arg.name == "self"
        ]
        mutable_returns = [
            ret
            for ret in self.returns
            if ret.annotation is not None and ret.annotation.is_write
        ]
        immutable_returns = [
            ret
            for ret in self.returns
            if ret.annotation is None or not ret.annotation.is_write
        ]
        # Some assertions: We don't want any functions with a return type of "-> (Tensor(a!), Tensor)",
        # because:
        # (1) It's more annoying to handle properly
        # (2) It's unnecessary - you can't method-chain on the first (mutated) output because it's part of a tuple.
        # Instead, we expect the (a!) argument to not be returned.
        if not (len(mutable_returns) == 0 or len(immutable_returns) == 0):
            raise AssertionError(
                f"NativeFunctions must have either only mutable returns, or only immutable returns. Found: {str(self)}"
            )
        for ret in mutable_returns:
            if not any(ret.annotation == arg.annotation for arg in out_and_self):
                raise AssertionError(
                    'All mutable returns must be aliased either to a keyword argument, or to "self". '
                    "Did you forget to mark an out argument as keyword-only?"
                )
        if self.arguments.out:
            # out= ops that return their mutable inputs are only really useful for method chaining.
            # And method chaining is only really useful if the thing you're returning is a plain Tensor.
            # So ideally, we'd enforce that out= ops with a single plain mutable tensor should return the tensor,
            # and all other types of out= op schemas should return void.
            # There are a bunch of existing out= ops that return tuples of tensors though, so we're stuck with allowing that.
            if any(a.type != BaseType(BaseTy.Tensor) for a in self.arguments.out):
                if len(self.returns) != 0:
                    raise AssertionError(
                        "out= ops that accept tensor lists as out arguments "
                        "are expected to have no return type (since you can't do method chaining on them)"
                    )
            else:
                # mutable keyword arguments whose name has _scratch_ prefix are
                # scratch tensors for memory planning and should not be returned
                non_scratch_out_args = len(
                    [
                        arg
                        for arg in self.arguments.out
                        if not arg.name.startswith("_scratch_")
                    ]
                )
                if non_scratch_out_args != len(self.returns):
                    raise AssertionError(
                        f"Must return as many arguments as there are out arguments, or no return at all. "
                        f"Got {non_scratch_out_args} non-scratch out args and {len(self.returns)} returns"
                    )

        if self.name.name.inplace:
            self_a = self.arguments.self_arg
            if not (
                self_a
                and self_a.argument.annotation
                and self_a.argument.annotation.is_write
            ):
                raise AssertionError(
                    f"Inplace op {self.name} must have a self argument with a mutable annotation"
                )
            if self_a.argument.type == BaseType(BaseTy.Tensor):
                # All inplace ops with an ordinary `Tensor self` argument should return self,
                # to allow for method chaining.
                if not (
                    len(self.returns) == 1
                    and self.returns[0].annotation == self_a.argument.annotation
                ):
                    raise AssertionError(
                        f"Inplace op {self.name} with Tensor self must return self"
                    )
            else:
                # You can't method chain on non-tensor self arguments though (like a list[Tensor])
                # so in all other cases we expect the return type to be none.
                if len(self.returns) != 0:
                    raise AssertionError(
                        f"Inplace op {self.name} with non-Tensor self must have no returns"
                    )

        if self.arguments.tensor_options is not None:
            if self.kind() != SchemaKind.functional:
                raise AssertionError(
                    "Found an operator that is not functional or out variant, but has tensor options arguments."
                    "This is not allowed- tensor options arguments are only allowed for factory functions."
                    f"schema: {str(self)}"
                )
        if self.is_functional_fn():
            if self.kind() != SchemaKind.functional:
                raise AssertionError(
                    "Found an operator that is not functional, but its overload contains the string 'functional'."
                    "This is a special keyword in the codegen, please use a different overload name."
                    f"schema: {str(self)}"
                )