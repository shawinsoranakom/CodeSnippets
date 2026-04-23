def reference_searchsorted(sorted_sequence, boundary, out_int32=False, right=False, side='left', sorter=None):
    side = 'right' if (right or side == 'right') else 'left'
    if len(sorted_sequence.shape) == 1 :
        ret = np.searchsorted(sorted_sequence, boundary, side=side, sorter=sorter)
        return ret.astype(np.int32) if out_int32 else ret
    elif sorted_sequence.shape[0] == 0:
        if sorter is not None:
            sorter = sorter.flatten()
        ret = np.searchsorted(sorted_sequence.flatten(), boundary.flatten(), side=side, sorter=sorter)
        ret = ret.astype(np.int32) if out_int32 else ret
        return ret.reshape(boundary.shape)
    else:
        # numpy searchsorted only supports 1D inputs so we split up ND inputs
        orig_shape = boundary.shape
        num_splits = np.prod(sorted_sequence.shape[:-1])
        splits = range(num_splits)
        sorted_sequence, boundary = sorted_sequence.reshape(num_splits, -1), boundary.reshape(num_splits, -1)
        if sorter is not None:
            sorter = sorter.reshape(num_splits, -1)

        split_sequence = [sorted_sequence[i] for i in splits]
        split_boundary = [boundary[i] for i in splits]
        split_sorter = [sorter[i] if (sorter is not None) else None for i in splits]

        split_ret = [np.searchsorted(s_seq, b, side=side, sorter=s_sort)
                     for (s_seq, b, s_sort) in zip(split_sequence, split_boundary, split_sorter, strict=True)]
        split_ret = [i.astype(np.int32) for i in split_ret] if out_int32 else split_ret
        return np.stack(split_ret).reshape(orig_shape)