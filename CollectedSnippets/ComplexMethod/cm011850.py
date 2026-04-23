def loader(index, reduction_index):
        assert len(reduction_index) == len(reduced_idx)
        if keepdims:
            assert len(index) == len(size)
            index = [index[i] for i in kept_idx]
        assert len(index) == len(kept_idx)
        new_index = [None] * (len(index) + len(reduction_index))
        for idx, var in itertools.chain(
            zip(kept_idx, index), zip(reduced_idx, reduction_index)
        ):
            new_index[idx] = var
        value = inner_loader(new_index)

        # For argmax/argmin, return tuple with logical linear index if needed
        if should_compute_logical_index:
            rindex = [sympy.expand(i) for i in reduction_index]

            # Compute linear index in row-major order
            # For reduction_ranges = [4, 6]: linear_index = r0 * 6 + r1
            linear_idx = rindex[0]
            for i in range(1, len(rindex)):
                linear_idx = linear_idx * reduced_sizes[i] + rindex[i]

            return (value, ops.index_expr(linear_idx, torch.int64))

        return value