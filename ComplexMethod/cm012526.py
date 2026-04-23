def _can_tile_cpu_tpu(self) -> bool:
        """Check if this kernel can use tiling on CPU/TPU.

        Tiling is compatible with reductions, transpositions, and multi-range-tree
        kernels as long as no flatten-based indexing is used (buf[...].flatten()[idx]).
        Flatten indexing requires global flat indices which don't decompose into
        per-tile local indices.

        Reject:
        - GPU (has its own TMA / padding path)
        - Flatten-based indexing
        - Scatter outputs (indirect indexing complicates tile boundaries)
        """
        if self.is_gpu:
            return False
        if self.has_flatten_indexing:
            return False
        if self.outputs_need_read:
            return False

        # If iteration variables appear in the compute body (not just in
        # load/store index resolution that collapses to [...]), tiling is
        # unsafe because the arange-based vars have full-tensor shapes.
        # Exception: vars emitted in tile-relative form are safe.
        if self.used_iter_vars:
            compute_text = "\n".join(str(line) for line in self.compute._lines)
            for var_sym in self.used_iter_vars:
                if var_sym in self.tile_relative_iter_vars:
                    continue
                if str(var_sym) in compute_text:
                    return False

        # Determine the reference output shape (highest-ndim output).
        out_bufs = list(self.args.output_buffers.keys())

        # Only check the current kernel's actual output buffers for transpose,
        # not _has_column_major_output() which scans all graph buffers and can
        # be triggered by unrelated intermediates (e.g., (N,1) reductions with
        # degenerate column-major strides).
        has_col_major_out = False
        for buf_name in out_bufs:
            info = self._get_buffer_info(buf_name)
            if info is None:
                continue
            _, buf_size, _, actual_strides, _ = info
            if len(actual_strides) >= 2 and len(buf_size) >= 2:
                s0 = actual_strides[0]
                s1 = actual_strides[1]
                d0 = self._safe_int(buf_size[0])
                d1 = self._safe_int(buf_size[1])
                if (
                    s0 is not None
                    and s1 is not None
                    and s0 < s1
                    and d0 is not None
                    and d1 is not None
                    and d0 > 1
                    and d1 > 1
                ):
                    has_col_major_out = True
                    break
        self.tile_has_transpose = bool(self.permuted_input_buffers) or has_col_major_out

        # Count trailing reduction dimensions in the output shape that must
        # not be tiled (the kernel body needs the full reduction range).
        # Only count when the kernel actually performs reduction (numel > 1).
        reduction_numel = self._compute_reduction_numel()
        has_reduction = reduction_numel is not None and reduction_numel > 1
        self.tile_skip_last_n = (
            sum(1 for tree in self.range_trees if tree.is_reduction)
            if has_reduction
            else 0
        )

        ref_shape: list[int] = []
        for buf_name in out_bufs:
            info = self._get_buffer_info(buf_name)
            if info is None:
                return False
            _, buf_size, _, _, _ = info
            int_size = [self._safe_int(s) for s in buf_size]
            if any(s is None for s in int_size):
                return False
            if len(int_size) > len(ref_shape):
                ref_shape = int_size  # type: ignore[assignment]

        if not ref_shape:
            return False

        # For collapsed permutation kernels, override ref_shape with the
        # collapsed output shape so all compatibility checks operate in
        # collapsed-shape space.
        if self.collapsed_output_shape is not None:
            ref_shape = list(self.collapsed_output_shape)

        ref_nd = len(ref_shape)

        all_bufs = list(self.args.input_buffers) + out_bufs
        has_tileable = False
        for buf_name in all_bufs:
            info = self._get_buffer_info(buf_name)
            if info is None:
                return False
            _, buf_size, _, _, _ = info
            if len(buf_size) == 0:
                continue  # scalar

            # Use collapsed shapes when available so dimension checks
            # operate in the same space as the kernel.
            if buf_name in self.collapsed_reshape_inputs:
                int_size = list(self.collapsed_reshape_inputs[buf_name])
            elif self.collapsed_output_shape is not None and buf_name in out_bufs:
                int_size = list(self.collapsed_output_shape)
            else:
                int_size = [self._safe_int(s) for s in buf_size]
                if any(s is None for s in int_size):
                    return False
            buf_nd = len(int_size)

            if buf_nd == ref_nd:
                # Same ndim: check dimensions match or are broadcast (1).
                # Allow strided buffers (dims may differ after reshape).
                is_strided = buf_name in self.strided_input_buffers
                mismatch = False
                for i in range(ref_nd):
                    if (
                        int_size[i] == ref_shape[i]
                        or int_size[i] == 1
                        or ref_shape[i] == 1
                        or is_strided
                    ):
                        continue
                    mismatch = True
                    break

                if mismatch and buf_name in self.permuted_input_buffers:
                    perm = self.permuted_input_buffers[buf_name]
                    if not (
                        len(perm) == ref_nd
                        and all(
                            int_size[perm[i]] == ref_shape[i]
                            or int_size[perm[i]] == 1
                            or ref_shape[i] == 1
                            for i in range(ref_nd)
                        )
                    ):
                        return False
                elif mismatch:
                    return False

                # At least one buffer with a tileable dim
                if is_strided or any(
                    int_size[i] == ref_shape[i] and ref_shape[i] > 1
                    for i in range(ref_nd)
                ):
                    has_tileable = True

            elif buf_nd > ref_nd:
                # Reduction input with extra dims. Find an alignment offset k
                # such that buf_shape[k+i] == ref_shape[i] for all i (skipping
                # broadcast dims where ref_shape[i] == 1).
                found = False
                for k in range(buf_nd - ref_nd + 1):
                    ok = True
                    for i in range(ref_nd):
                        if ref_shape[i] == 1:
                            continue
                        if int_size[k + i] != ref_shape[i]:
                            ok = False
                            break
                    if ok:
                        found = True
                        break
                if not found:
                    return False
                has_tileable = True

            else:
                # Fewer dims: verify numpy-style broadcastability
                for a, b in zip(reversed(int_size), reversed(ref_shape)):
                    if a != b and a != 1 and b != 1:
                        return False

        if not has_tileable:
            return False

        # On CPU (interpret mode) each tile iteration has significant
        # Python/JAX overhead, so cap the grid size.  Store the cap
        # so _codegen_tiled_specs can pass it to pallas_compute_tiling,
        # which will scale up tiles to stay within the limit.
        is_tpu = V.graph.get_current_device_or_throw().type == "tpu"
        if not is_tpu:
            self._cpu_max_grid_product = 64
        else:
            self._cpu_max_grid_product = None

        return True