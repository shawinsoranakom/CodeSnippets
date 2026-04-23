def kind(self) -> SchemaKind:
        """
        What kind of schema is this?  A functional schema is one
        that returns a newly allocated output; an inplace schema
        modifies the self argument inplace; an out schema writes
        the result into an explicitly provided out argument.
        """
        is_out = bool(self.arguments.out)
        is_scratch = bool(
            [arg for arg in self.arguments.out if arg.name.startswith("_scratch_")]
        )
        is_inplace = self.name.name.inplace
        is_mutable = any(
            a.annotation is not None and a.annotation.is_write
            for a in self.arguments.post_self_positional
        )
        if is_out and is_inplace:
            raise AssertionError("A schema cannot be both out= and inplace")
        # out= and inplace schemas can also have post_self_positional mutable args,
        # but we give precedence to out= and inplace when deciding the schema kind.
        # Tradeoff: we probably don't want to have to teach codegen that looks at inplace ops
        # to also worry about mutable post_self_positional arguments,
        # but it seems like a much bigger lift to classify them has having a new schema kind.
        # The number of ops that fit in this strange category is small enough that
        # we can probably manually write code for them instead of forcing the codegen to handle them.
        if is_inplace:
            return SchemaKind.inplace
        elif is_scratch:
            if not is_out:
                raise AssertionError(
                    "invariant: all scratch operators are expected to be out= operators too"
                )
            return SchemaKind.scratch
        elif is_out:
            if is_scratch:
                raise AssertionError(
                    "We should not categorize a scratch op as an out variant. Check if the order of if statements are expected!"
                )
            return SchemaKind.out
        elif is_mutable:
            return SchemaKind.mutable
        else:
            return SchemaKind.functional