def should_swap(idx_a, idx_b):
        def ge(a, b):
            """
            Returns true if a is symbolically greater than or equal to b, assuming a >= 0, b >= 0.
            """
            if guard_or_false(b == 0):
                return True
            elif guard_or_false(a == 0):
                return False
            return guard_or_false(a >= b) or guard_or_false(a % b == 0)

        for tensor in tensors:
            stride_a = tensor.stride()[idx_a]
            stride_b = tensor.stride()[idx_b]

            if guard_or_false(stride_a == 0) or guard_or_false(stride_b == 0):
                continue

            if guard_or_false(stride_a == stride_b):
                if ge(shape[idx_b], shape[idx_a]):
                    continue
                return 1

            if ge(stride_b, stride_a):
                return -1

            if ge(stride_a, stride_b):
                return 1

        # Note: this case is hit if all strides are zero,
        # or all strides are equal and all dimensions have the same length
        return 0