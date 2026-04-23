def try_outer_loop_fusion_with_local_buf(node: OuterLoopFusedSchedulerNode):
            """
            Codegen code with fused outer loop and local Buffer.
            """
            assert isinstance(node, OuterLoopFusedSchedulerNode)
            cpp_kernel_proxy_list.clear()
            nodes_list.clear()

            def get_call_ranges(node: BaseSchedulerNode):
                assert isinstance(node, (SchedulerNode, FusedSchedulerNode))
                nodes: list[SchedulerNode] = node.get_nodes()  # type: ignore[assignment]
                _, (group, reduction_group) = max(
                    nodes, key=lambda x: int(x.is_reduction())
                ).group
                call_ranges = tuple(group) + tuple(reduction_group)
                return call_ranges

            local_buffers: list[ir.Buffer] = []
            # Map local buffer name to a list of global buffers
            local_to_global_buffers: dict[str, list[ir.Buffer]] = {}
            if all(
                len(get_call_ranges(_node)) == node.outer_loop_fusion_depth + 1
                for _node in node.get_outer_nodes()
            ):
                # Ref to the typical case of local buffer in
                # https://github.com/pytorch/pytorch/blob/1115a25c36340554442f28f9570abd42f0aface2/aten/src/ATen/native/cpu/SoftMaxKernel.cpp#L159
                # where the buffer is with size of last dim and contiguous.
                # Only support this typical case at first.
                visited_scheduler_nodes: OrderedSet[str] = OrderedSet()
                for scheduler_node in node.get_nodes():
                    # all users inside same OuterLoopFusedSchedulerNode
                    assert isinstance(scheduler_node, SchedulerNode)
                    visited_scheduler_nodes.add(scheduler_node.get_name())
                    if (
                        scheduler_node.is_reduction()
                        or len(scheduler_node.get_outputs()) != 1
                    ):
                        continue

                    scheduler_buffer = scheduler_node.get_outputs()[0]
                    if all(
                        user.node in node.get_nodes() for user in scheduler_buffer.users
                    ):
                        global_buffer = scheduler_buffer.node
                        assert isinstance(global_buffer, ir.ComputedBuffer)
                        global_buffer_layout = global_buffer.get_layout()
                        size_offset = node.outer_loop_fusion_depth - len(
                            get_call_ranges(scheduler_node)
                        )

                        def is_all_write_read_contiguous():
                            contiguous_index_expr = 0
                            stride = 1
                            for var, range in reversed(
                                # pyrefly: ignore [missing-attribute]
                                scheduler_node._body.var_ranges.items()
                            ):
                                contiguous_index_expr += stride * var
                                stride *= range
                            # pyrefly: ignore [missing-attribute]
                            write_index_expr = scheduler_node._body.get_write_expr(
                                scheduler_buffer.get_name()
                            )

                            def is_contiguous_index(x):
                                return x == contiguous_index_expr

                            return is_contiguous_index(write_index_expr) and all(
                                isinstance(user.node, SchedulerNode)
                                and is_contiguous_index(
                                    user.node._body.get_read_expr(
                                        scheduler_buffer.get_name()
                                    ),
                                )
                                for user in scheduler_buffer.users
                            )

                        if not (
                            global_buffer_layout.is_contiguous()
                            and is_all_write_read_contiguous()
                        ):
                            continue
                        # Local Buffer is a view of global buffer
                        local_buffer_stride: list[int] = []
                        stride = global_buffer_layout.stride[-1]
                        local_buffer_size = get_call_ranges(scheduler_node)[
                            size_offset:
                        ]
                        for sz in reversed(local_buffer_size):
                            local_buffer_stride.insert(0, stride)
                            stride *= sz
                        local_buffer_layout = ir.FixedLayout(
                            global_buffer_layout.device,
                            global_buffer_layout.dtype,
                            local_buffer_size,
                            local_buffer_stride,
                        )

                        def try_share_local_buffer(local_buffer_layout, local_buffers):
                            for local_buf in local_buffers:
                                if local_buffer_layout == local_buf.layout and all(
                                    all(
                                        user.node.get_name() in visited_scheduler_nodes
                                        for user in V.graph.scheduler.name_to_buf[
                                            global_buffer.name
                                        ].users
                                    )
                                    for global_buffer in local_to_global_buffers[
                                        local_buf.name
                                    ]
                                    if global_buffer.name is not None
                                ):
                                    return local_buf
                            return None

                        local_buf_prefix = "local_buffer_data"
                        # Share existing local buffer
                        local_buffer_used = try_share_local_buffer(
                            local_buffer_layout, local_buffers
                        )
                        if not local_buffer_used:
                            # Create new local buffer
                            local_buffer_used = ir.Buffer(
                                name=f"{local_buf_prefix}_{len(local_buffers)}",
                                layout=local_buffer_layout,
                            )
                            local_buffers.append(local_buffer_used)
                            local_to_global_buffers[local_buffer_used.name] = []  # type: ignore[index]

                        local_to_global_buffers[local_buffer_used.name].append(
                            global_buffer,
                        )

            with LocalBufferContext(kernel_group.args) as scope:
                if len(local_buffers) > 0:
                    for local_buffer in local_buffers:
                        assert local_buffer.name is not None
                        scope.add_local_buffer(
                            local_buffer, local_to_global_buffers[local_buffer.name]
                        )
                for _node in node.get_outer_nodes():
                    assert isinstance(_node, (FusedSchedulerNode, SchedulerNode))
                    cpp_kernel_proxy = self.kernel_proxy_cls(kernel_group)
                    cpp_kernel_proxy.codegen_nodes(_node.get_nodes())  # type: ignore[arg-type]
                    cpp_kernel_proxy_list.append(cpp_kernel_proxy)
                    nodes_list.append(_node.get_nodes())  # type: ignore[arg-type]

                if not node.check_outer_fusion_loop_level_attr(
                    cpp_kernel_proxy_list, node.outer_loop_fusion_depth
                ):
                    for removed_buffer in scope.removed_buffers:
                        # Restore the removed buffers by this context before
                        # fallback to codegen without using Local Buffer
                        V.graph.removed_buffers.remove(removed_buffer)
                    return False
                metrics.cpp_outer_loop_fused_inner_counts.append(
                    metrics.CppOuterLoopFusedCount(
                        len(cpp_kernel_proxy_list),
                        local_buffer_number=len(scope.local_buffers),
                    )
                )
                outer_fusion_cpp_kernel_proxy = node.merge_outer_fusion_kernels(
                    cpp_kernel_proxy_list,
                )
                kernel_group.finalize_kernel(
                    outer_fusion_cpp_kernel_proxy,
                    [*itertools.chain.from_iterable(nodes_list)],
                )

            return True