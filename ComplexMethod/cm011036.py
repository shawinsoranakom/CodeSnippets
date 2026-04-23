def composition(layoutA: Layout, layoutB: LayoutInput) -> Layout:
    if layoutB is None:
        return layoutA
    elif is_int(layoutB):
        return composition(layoutA, Layout(layoutB))
    elif is_tuple(layoutB):
        if len(layoutA) < len(layoutB):
            raise AssertionError
        return make_layout(
            # pyrefly: ignore [bad-argument-type]
            chain(
                (composition(layoutA[i], layoutB[i]) for i in range(len(layoutB))),  # type: ignore[arg-type]
                (layoutA[i] for i in range(len(layoutB), len(layoutA))),
            )
        )
    elif is_tuple(layoutB.shape):
        return make_layout(composition(layoutA, layoutB_i) for layoutB_i in layoutB)  # type: ignore[arg-type, attr-defined]

    if layoutB.stride == 0:
        return Layout(layoutB.shape, 0)
    else:
        result_shape = []
        result_stride = []
        rest_shape = layoutB.shape
        rest_stride = layoutB.stride
        flat_A = coalesce(layoutA)
        # when left layout is multi-dimensional sublayout, aka, self = (a,b,...,c):(x,y,...,z), layout = s:d,
        # for integral s and d means that we want:
        # (1) “remove” the first d elements from left, starting from rightmost. (This will increase the stride.)
        # (2) “keep” the first s of those strided elements. (This does not affect the stride.)
        # For example, if self = (6,2):(2,1), layout = (3:2)
        # Step 1: remove the first 2 elements from self with stride increase, i.e., (6,2):(2,1) -> (6,1):(2,2)
        # Step 2: keep the first 3 of those strided elements, i.e., (6,1):(2,2) -> (3,1):(2,2)
        # Because we are going lexicographically, we go through left layout from right to left.
        for curr_shape, curr_stride in zip(
            reversed(flatten(flat_A.shape)[1:]), reversed(flatten(flat_A.stride)[1:])
        ):
            if not (curr_shape % rest_stride == 0 or rest_stride % curr_shape == 0):  # type: ignore[operator]
                raise AssertionError
            new_shape = min(max(1, curr_shape // rest_stride), rest_shape)  # type: ignore[operator]

            if new_shape != 1:
                result_shape.append(new_shape)  # Append to end, will reverse later
                result_stride.append(rest_stride * curr_stride)

            rest_shape = rest_shape // new_shape  # type: ignore[operator]
            rest_stride = -(
                -rest_stride // curr_shape  # type: ignore[operator]
            )  # Python exclusive impl: "//" is always floor div so == ceil_div(abs(rest_stride), curr_shape) * signum(rest_stride)

        # When left has single-size sublayout or reach the last sublayout, aka, left = a:b, layout = s:d,
        # the result is rather trivial: left o layout = a:b o s:d = s:(b*d).
        # For example, if self = (6:2), layout = (3:2), the result is (3:(2*2)) = (3:4).
        if rest_shape != 1 or len(result_shape) == 0:
            result_shape.append(rest_shape)  # Append to end, will reverse later
            result_stride.append(rest_stride * flatten(flat_A.stride)[0])

        # Reverse the lists because we build lists in reverse order (append to end), this way it is more efficient.
        result_shape.reverse()
        result_stride.reverse()

        if len(result_shape) == 1:
            return Layout(result_shape[0], result_stride[0])  # type: ignore[arg-type]
        else:
            return Layout(tuple(result_shape), tuple(result_stride))