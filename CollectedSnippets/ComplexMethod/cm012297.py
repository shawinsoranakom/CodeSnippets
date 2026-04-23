def slice_noop(self, dim=0, start=None, end=None, step=1):
    if _needs_spmd_graph_preservation():
        # Keep no-op slices so all ranks produce identical FX graphs (SPMD)
        # with matching op counts and runtime estimations.
        return False
    if start is None or end is None:
        return False

    slice_dim_size = self.shape[dim]
    if (
        statically_known_true(sym_eq(start, 0))
        and (
            statically_known_true(end >= 2**63 - 1)
            or statically_known_true(end >= slice_dim_size)
        )
        and statically_known_true(sym_eq(step, 1))
    ):
        return True
    return False