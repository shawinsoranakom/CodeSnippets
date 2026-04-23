def simulate_codegen(self) -> None:
        from .simd import SIMDKernel

        kernel_size_outside_loop = (*self.groups[:-1], sympy.S.One)
        kernel_size_inside_loop = tuple(self.groups)
        self.kernel_sizes = kernel_size_inside_loop

        for node in self.features.node_schedule:
            if node is DisableReduction:
                self.inside_reduction = False
                self.kernel_sizes = kernel_size_outside_loop
                continue
            elif node is EnableReduction:
                self.inside_reduction = True
                self.kernel_sizes = kernel_size_inside_loop
                self.loops.append(MemoryEstimate())
                continue
            assert isinstance(node, SchedulerNode)
            rw = extract_loop_body_with_args(
                node._body,
                SIMDKernel.map_kernel_groups_to_node_sizes(
                    self.kernel_sizes, node.get_ranges(), self.set_ranges
                ),
                dict(zip(self.symbols, self.kernel_sizes)),
            )

            for dep in rw._reads:
                if not isinstance(dep, MemoryDep):
                    continue
                dep = dep.simplify_with_ranges()
                if not self.persistent.writes.get(dep.name):  # cache miss?
                    self.persistent.reads[dep.name].add(dep)
                # the cache behavior of looped kernels is more complex than the persistent case above
                # some operations are lifted outside the loop (if they don't use the reduction dimension)
                # other operations are inside the loop, and can only be reused within the same loop
                if not (
                    self.outside_loop.writes.get(dep.name)
                    or self.loops[-1].writes.get(dep.name)
                ):
                    self.scope(dep).reads[dep.name].add(dep)
                    if dep.name in self.store_buffer_names and self.loops[-1].reads.get(
                        dep.name
                    ):
                        self.must_keep_buffers.add(dep.name)

            for dep in rw._writes:
                if not isinstance(dep, MemoryDep):
                    continue
                dep = dep.simplify_with_ranges()
                self.store_buffer_names.add(dep.name)
                self.persistent.writes[dep.name].add(dep)
                self.scope(dep).writes[dep.name].add(dep)