def lookup_collective(
        self,
        collective_name: str,
        pg_ranks: tuple[int, ...],
        nelems: int,
        dtype: str,
    ) -> tuple[float, str] | None:
        """Look up collective duration in ms. Returns (duration_ms, source) or None.

        ``source`` is ``"profile"`` for exact/interpolated matches, or
        ``"pg_bandwidth"`` when bandwidth-based extrapolation was used.

        Tries exact rank match first, then falls back to mesh-dimension match
        (e.g. (0,2,4,6) and (1,3,5,7) both have stride=2, size=4 → same mesh dim).

        When the target size exceeds EXTRAPOLATION_CAP * max_observed, uses
        bandwidth-based estimation from peak observed bandwidth instead of
        linear extrapolation (which overestimates for large messages).
        """
        norm_name = self._normalize_collective_name(collective_name)
        # Try exact rank match first
        key = (norm_name, pg_ranks, dtype)
        entries = self._collective_index.get(key)
        if not entries:
            # Fall back to mesh-dimension match
            gs = len(pg_ranks)
            stride = _rank_stride(pg_ranks)
            if (
                stride is not None
                and self._pg_count_by_mesh_dim.get((stride, gs), 0) == 1
            ):
                mesh_dim_key = (norm_name, stride, gs, dtype)
                entries = self._collective_index_by_mesh_dim.get(mesh_dim_key)
            if not entries:
                return None

        # Exact match
        for n, dur in entries:
            if n == nelems:
                return (dur / 1e3, "profile")  # us -> ms

        # Check extrapolation distance: if target is far beyond observed range,
        # use bandwidth-based model instead of log-log extrapolation
        max_observed = max((n for n, _ in entries if n > 0), default=0)
        if max_observed > 0 and nelems > max_observed * self.EXTRAPOLATION_CAP:
            est = self._estimate_with_pg_bandwidth(pg_ranks, nelems, dtype)
            if est is not None:
                return (est, "pg_bandwidth")
            # Fall through to log-log if no BW data available

        # Interpolation in log-log space
        result = self._interpolate_log_log(entries, nelems)
        if result is not None:
            return (result, "profile")
        return None