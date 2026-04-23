def codegen_functions(self, fn_list, var_sizes_list):
        assert len(fn_list) == len(var_sizes_list)
        kernel_group = self.kernel_group
        group, reduction_group = max(var_sizes_list, key=lambda sizes: len(sizes[1]))

        self.set_ranges(group, reduction_group)

        def codegen_kernel(cls, *args):
            with kernel_group.new_kernel(cls, *args) as kernel:
                # Ugly hack to maintain the metrics kernel count since
                # we only count in CppKernelProxy, not those contained in it
                # pyrefly: ignore [bad-assignment]
                metrics.generated_kernel_count -= 1

                run(kernel)
                return kernel

        def run(kernel):
            vars, reduction_vars = kernel.set_ranges(group, reduction_group)
            in_suffix = False
            for fn, var_sizes in zip(fn_list, var_sizes_list):
                if var_sizes in [
                    (group, reduction_group),
                    (tuple(itertools.chain(group, reduction_group)), ()),
                ]:
                    assert not in_suffix
                    fn(vars, reduction_vars)
                else:
                    in_suffix = True
                    assert var_sizes == (
                        group,
                        (),
                    ), f"unexpected group: {var_sizes} != {group}, {reduction_group}"
                    # we can fuse in some extra pointwise into the suffix
                    with kernel.write_to_suffix():
                        fn(vars, ())

        scalar_kernel = codegen_kernel(self.kernel_cls)
        V.graph.removed_buffers |= scalar_kernel.removed_buffers
        V.graph.inplaced_to_remove |= scalar_kernel.inplaced_to_remove
        self.loop_nest = LoopNest.build(scalar_kernel)

        if not self.picked_vec_isa or not self.itervars:
            self.kernels = [scalar_kernel]
            self.aggregate_reduction_buffers(False, None)
            self.loop_nest.set_kernel(self)
            return

        # Kernels share the same global contexts like V.graph.wrapper_code, V.kernel.args.
        # But the generated scalar kernel has updated these global contexts. Hence, the other kernels
        # should not do this again to avoid context conflict. By now, we only control the
        # config.inplace_buffers. In the future, we could maintain more contexts.
        with torch._inductor.config.patch(inplace_buffers=False):
            tiling_select = TilingSelect()
            tiling_factors, tiling_indices = tiling_select.select_tiling(
                fn_list, var_sizes_list
            )
            assert len(tiling_factors) == len(tiling_indices)
            _inner_loop_reduction_outer_not = False
            _outer_loop = None
            if tiling_indices:
                inner_loop_reduction = False
                outer_loop_level = tiling_indices[0]
                inner_loop_level = outer_loop_level + 1
                if len(self.loop_nest.loops) > inner_loop_level:
                    inner_loop_reduction = self.loop_nest.loops[
                        inner_loop_level
                    ].is_reduction
                    outer_loop_reduction = self.loop_nest.loops[
                        outer_loop_level
                    ].is_reduction
                    _inner_loop_reduction_outer_not = (
                        inner_loop_reduction and not outer_loop_reduction
                    )

            if len(tiling_indices) == 1:
                # pyrefly: ignore [bad-assignment]
                metrics.generated_cpp_vec_kernel_count += 1
                loop = self.loop_nest.tile(tiling_indices[0], factor=tiling_factors[0])
                vec_kernel = codegen_kernel(
                    self.vec_kernel_cls, tiling_factors[0], tiling_indices[0]
                )
                tail_size = loop.size - loop.tiled_size
                vec_kernel.active_ranges = {loop.var: (0, loop.tiled_size)}
                if config.cpp.enable_loop_tail_vec:
                    tail_kernel = codegen_kernel(
                        self.vec_kernel_cls,
                        tiling_factors[0],
                        tiling_indices[0],
                        tail_size,
                    )
                else:
                    tail_kernel = scalar_kernel
                    scalar_kernel.inner_itervars = [loop.var]
                tail_kernel.active_ranges = {loop.var: (loop.tiled_size, loop.size)}
                self.kernels = [vec_kernel, tail_kernel]
                _outer_loop = loop
            elif len(tiling_indices) == 2:
                assert (
                    tiling_indices[1] == len(self.itervars) - 1
                    and tiling_factors[0] == tiling_factors[1]
                )

                # pyrefly: ignore [bad-assignment]
                metrics.generated_cpp_vec_kernel_count += 2
                outer_loop = self.loop_nest.tile(
                    tiling_indices[0], factor=tiling_factors[0]
                )
                outer_ranges = {
                    "main": (0, outer_loop.tiled_size),
                    "tail": (outer_loop.tiled_size, outer_loop.size),
                }
                outer_tail_size = outer_loop.size - outer_loop.tiled_size
                inner_loop = self.loop_nest.tile(
                    tiling_indices[1], factor=tiling_factors[0]
                )
                inner_ranges = {
                    "main": (0, inner_loop.tiled_size),
                    "tail": (inner_loop.tiled_size, inner_loop.size),
                }
                inner_tail_size = inner_loop.size - inner_loop.tiled_size
                tile2d_kernel = codegen_kernel(
                    self.tile2d_kernel_cls,
                    tiling_factors[0],
                    tiling_indices,
                )
                tile2d_kernel.active_ranges = {
                    outer_loop.var: outer_ranges["main"],
                    inner_loop.var: inner_ranges["main"],
                }
                tail_kernel = []
                if config.cpp.enable_loop_tail_vec:
                    for outer_r, inner_r in (
                        ("main", "tail"),
                        ("tail", "main"),
                        ("tail", "tail"),
                    ):
                        _inner_tail_size = (
                            inner_tail_size if inner_r == "tail" else None
                        )
                        _outer_tail_size = (
                            outer_tail_size if outer_r == "tail" else None
                        )
                        kernel = codegen_kernel(
                            self.tile2d_kernel_cls,
                            tiling_factors[0],
                            tiling_indices,
                            _inner_tail_size,
                            _outer_tail_size,
                        )
                        kernel.active_ranges = {
                            outer_loop.var: outer_ranges[outer_r],
                            inner_loop.var: inner_ranges[inner_r],
                        }
                        tail_kernel.append(kernel)
                else:
                    vec_kernel = codegen_kernel(
                        self.vec_kernel_cls, tiling_factors[0], tiling_indices[0]
                    )
                    vec_kernel.active_ranges = {
                        outer_loop.var: outer_ranges["main"],
                        inner_loop.var: inner_ranges["tail"],
                    }
                    vec_kernel.inner_itervars = [inner_loop.var]
                    tail_kernel.append(vec_kernel)
                    scalar_kernel.active_ranges = {
                        outer_loop.var: outer_ranges["tail"],
                        inner_loop.var: (0, inner_loop.size),
                    }
                    scalar_kernel.inner_itervars = [inner_loop.var, outer_loop.var]
                    tail_kernel.append(scalar_kernel)
                self.kernels = [tile2d_kernel] + tail_kernel
                _outer_loop = outer_loop
            else:
                self.kernels = [scalar_kernel]
            self.aggregate_reduction_buffers(
                _inner_loop_reduction_outer_not, _outer_loop
            )
            self.loop_nest.set_kernel(self)