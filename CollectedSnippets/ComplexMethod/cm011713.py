def index_cmp(a: int, b: int) -> int:
        if sizes[a] == 1 or sizes[b] == 1:
            # 1-sizes don't matter, just move them to the end
            return cmp(sizes[a] == 1, sizes[b] == 1)

        # Take abs, otherwise flipped dimensions are treated as smaller
        # strides than contiguous dims
        stride_len_a = [abs(sl[a]) for sl in stride_lengths]
        stride_len_b = [abs(sl[b]) for sl in stride_lengths]

        # equivalent to
        # np.logical_or(stride_lengths[:, b] == 0, stride_lengths[:, a] < stride_lengths[:, b]).all()
        a_first = sum(
            sl_b == 0 or sl_a < sl_b for sl_a, sl_b in zip(stride_len_a, stride_len_b)
        )
        b_first = sum(
            sl_a == 0 or sl_b < sl_a for sl_a, sl_b in zip(stride_len_a, stride_len_b)
        )
        if a_first > b_first:
            return -1
        if b_first > a_first:
            return 1

        # otherwise contiguous
        return cmp(b, a)