def _build_indices(self) -> None:
        """Build lookup indices from parsed records."""
        coll_idx: dict[tuple[str, tuple[int, ...], str], list[tuple[int, float]]] = (
            defaultdict(list)
        )
        coll_idx_by_mesh_dim: dict[
            tuple[str, int, int, str], list[tuple[int, float]]
        ] = defaultdict(list)
        # Track distinct PG rank sets per mesh dimension for ambiguity check
        pg_sets_by_mesh_dim: dict[tuple[int, int], OrderedSet[tuple[int, ...]]] = (
            defaultdict(OrderedSet)
        )
        for rec in self.collectives:
            norm_name = self._normalize_collective_name(rec.collective_name)
            gs = len(rec.pg_ranks) if rec.pg_ranks else rec.group_size
            coll_idx[(norm_name, rec.pg_ranks, rec.dtype)].append(
                (rec.out_nelems, rec.duration_us)
            )
            stride = _rank_stride(rec.pg_ranks)
            if stride is not None:
                coll_idx_by_mesh_dim[(norm_name, stride, gs, rec.dtype)].append(
                    (rec.out_nelems, rec.duration_us)
                )
                pg_sets_by_mesh_dim[(stride, gs)].add(rec.pg_ranks)
        # Sort by nelems for interpolation
        self._collective_index = {
            k: sorted(v, key=lambda x: x[0]) for k, v in coll_idx.items()
        }
        self._collective_index_by_mesh_dim = {
            k: sorted(v, key=lambda x: x[0]) for k, v in coll_idx_by_mesh_dim.items()
        }
        self._pg_count_by_mesh_dim = {
            k: len(pgs) for k, pgs in pg_sets_by_mesh_dim.items()
        }

        op_groups: defaultdict[
            tuple[
                str,
                tuple[tuple[int, ...], ...],
                tuple[tuple[int, ...], ...],
                torch.dtype | None,
            ],
            list[float],
        ] = defaultdict(list)
        for rec in self.ops:
            key = (rec.op_name, rec.input_shapes, rec.input_strides, rec.dtype)
            op_groups[key].append(rec.duration_us)
        self._op_index = {k: sum(v) / len(v) for k, v in op_groups.items()}

        # Per-PG peak bandwidth: compute bytes/us for each collective observation,
        # then take the max from the top-N largest messages per PG (where bandwidth
        # is most representative of hardware speed, not dominated by startup latency).
        # Uses output-convention bytes (matching _estimate_with_pg_bandwidth).
        _TOP_N = 5  # consider top N largest messages for peak BW
        pg_bw_samples: dict[tuple[int, ...], list[tuple[int, float]]] = defaultdict(
            list
        )
        mesh_dim_bw_samples: dict[tuple[int, int], list[tuple[int, float]]] = (
            defaultdict(list)
        )
        for rec in self.collectives:
            if rec.out_nelems <= 0 or rec.duration_us <= 0:
                continue
            gs = len(rec.pg_ranks) if rec.pg_ranks else rec.group_size
            elem_bytes = self._dtype_elem_bytes(rec.dtype)
            total_bytes = rec.out_nelems * elem_bytes
            bw_gbps = total_bytes / (rec.duration_us * 1e-6) / 1e9  # GB/s
            pg_bw_samples[rec.pg_ranks].append((total_bytes, bw_gbps))
            stride = _rank_stride(rec.pg_ranks)
            if stride is not None:
                mesh_dim_bw_samples[(stride, gs)].append((total_bytes, bw_gbps))

        def _peak_bw_from_samples(
            samples: list[tuple[int, float]],
        ) -> float:
            """Get peak BW from the top-N largest messages."""
            # Sort by message size descending, take top N, return max BW
            sorted_samples = sorted(samples, key=lambda x: x[0], reverse=True)
            top = sorted_samples[:_TOP_N]
            return max(bw for _, bw in top) if top else 0.0

        self._pg_peak_bw = {
            pg: _peak_bw_from_samples(samples)
            for pg, samples in pg_bw_samples.items()
            if samples
        }
        self._mesh_dim_peak_bw = {
            key: _peak_bw_from_samples(samples)
            for key, samples in mesh_dim_bw_samples.items()
            if samples
        }