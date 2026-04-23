def coalesce(self) -> "_MeshLayout":
        """
        A layout is represented by (sizes):(strides), e.g. (3,2):(4,2).
        Two consecutive dimensions can be "merged" into one if their
        strides are contiguous/multiplicative (i.e., the inner stride * inner size
        equals the next stride), we perform this kind of merge inside coalesce.

        Example 1 (simple): (3,2):(2,1)
        - inner dimension: has stride=1, size=2
        - outer dimension: stride = inner_stride * inner_size = 2
        → coalesced = (6:1)    # acts like a flat 1D array of length 6

        Example 2 (non-coalescible): (3,2):(4,1)
        - inner dimension: stride=1, size=2 → 2*1 = 2
        - outer dimension: stride=4, mismatch (≠ 2)
        → cannot merge; result stays (3,2):(4,1)
        """
        layout = coalesce(self)
        # The original PuCute coalesce() will use stride=0 for size=1 for all dimension.
        # We don't want to do that in device mesh, we will reset them to be 1 to be same as PyTorch.
        if is_int(layout.stride) and layout.stride == 0:
            return _MeshLayout(layout.shape, 1)
        elif is_tuple(layout.stride) and any(s == 0 for s in layout.stride):
            non_zero_strides = tuple(s if s != 0 else 1 for s in layout.stride)
            return _MeshLayout(layout.shape, non_zero_strides)
        else:
            return _MeshLayout(layout.shape, layout.stride)