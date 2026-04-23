def _interleave(a, b, axis):
        """Given two Tensors of static shape, interleave them along axis."""
        if not (
            a.shape[axis] == b.shape[axis] or a.shape[axis] == b.shape[axis] + 1
        ):
            raise ValueError(
                "Shapes are incompatible for associative_scan interleaving. "
                f"a.shape[{axis}]={a.shape[axis]}, "
                f"b.shape[{axis}]={b.shape[axis]}"
            )

        # we want to get a: [a1, a2], b: [b1, b2]
        # to a: [a1, 0, a2, 0], b: [0, b1, 0, b2]
        a_shape = list(a.shape)
        a_shape[axis] = a.shape[axis] * 2 - 1

        b_shape = list(b.shape)
        b_shape[axis] = b.shape[axis] * 2 - 1

        a_dil = torch.zeros(a_shape)
        slice_along_axis(a_dil, 0, None, 2, axis).copy_(a)

        b_dil = torch.zeros(b_shape)
        slice_along_axis(b_dil, 0, None, 2, axis).copy_(b)

        a_pad = [[0, 0] for _ in range(a.dim())]
        a_pad[axis][-1] = 1 if a.shape[axis] == b.shape[axis] else 0
        a_pad = a_pad[::-1]
        a_pad = tree.flatten(a_pad)

        b_pad = [[0, 0] for _ in range(b.dim())]
        b_pad[axis] = [1, 0] if a.shape[axis] == b.shape[axis] else [1, 1]
        b_pad = b_pad[::-1]
        b_pad = tree.flatten(b_pad)

        op = torch.bitwise_or if a.dtype == torch.bool else torch.add
        return op(
            torch.nn.functional.pad(a_dil, a_pad),
            torch.nn.functional.pad(b_dil, b_pad),
        )