def eval(cls, *args):
        if len(args) % 2 != 0:
            raise AssertionError(
                f"expected an even number of arguments, got {len(args)}"
            )
        dim = len(args) // 2
        sizes = args[0:dim]
        strides = args[dim:]

        # sym_node imported in torch.__init__. Local import to avoid an import cycle
        from torch.fx.experimental.symbolic_shapes import (
            eval_is_non_overlapping_and_dense,
        )

        if all(isinstance(a, sympy.Integer) for a in args):
            return eval_is_non_overlapping_and_dense(
                [int(a) for a in sizes], [int(a) for a in strides]
            )

        if dim == 1:
            # Manually implement the rank one short circuit
            if strides[0].is_Number and strides[0] == 1:
                return 1

            if sizes[0].is_Number and sizes[0] < 2:
                return 1

            # return 0 case covered by case above

            # TODO: Inability to access size-obliviousness sucks: if we have a
            # size oblivious test on a size-like unbacked SymInt, we could
            # confidently return zero when we have a size-like u0 stride
            # and a size-like u1 size.  Maybe a fancy ValueRanges analysis for
            # this function could help figure this out.

        if all(isinstance(a, sympy.Integer) for a in strides):
            if dim == 0:
                raise AssertionError("dim must not be zero")
            # When all strides are integral, we can sort, and the size for the
            # largest stride doesn't matter and can be arbitrarily symbolic
            s_sizes, s_strides = zip(
                *sorted(zip(sizes, strides, strict=True), key=operator.itemgetter(1)),
                strict=True,
            )
            # Put something arbitrary in the max size spot, it'll be ignored
            if all(isinstance(a, sympy.Integer) for a in s_sizes[:-1]):
                s_sizes = s_sizes[:-1] + (42,)
                # We can reuse the regular eval, because it is invariant to
                # permutation of dimensions
                return eval_is_non_overlapping_and_dense(
                    [int(a) for a in s_sizes], [int(a) for a in s_strides]
                )

        return None