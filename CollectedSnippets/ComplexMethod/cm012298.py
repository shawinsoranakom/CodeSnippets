def slice_scatter_noop(self, src, dim=0, start=None, end=None, step=1):
    if start is None:
        start = 0
    if end is None:
        end = 2**63 - 1
    slice_scatter_dim_size = self.shape[dim]
    if (
        self.shape == src.shape
        and start == 0
        and (
            statically_known_true(end >= 2**63 - 1)
            or statically_known_true(end >= slice_scatter_dim_size)
        )
        and step == 1
    ):
        return True
    return False