def codegen_comment(self, node_schedule, kernel_name=None):
        wrapper = V.graph.wrapper_code
        origins, _detailed_origins = get_kernel_metadata(node_schedule, wrapper)
        if origins:
            wrapper.make_comment(origins)

        if config.debug_fusion:
            from torch._inductor.scheduler import (
                BaseSchedulerNode,
                ForeachKernelSchedulerNode,
            )

            if not any(
                isinstance(n, ForeachKernelSchedulerNode) for n in node_schedule
            ):
                # We probably should look what are the nodes inside a foreach
                # schedule node
                node_names = [
                    n.get_name()
                    for n in node_schedule
                    if isinstance(n, BaseSchedulerNode)
                ]
                wrapper.make_comment(
                    f"{wrapper.comment} Fused node name list: {', '.join(node_names)}"
                )

        if kernel_name:
            debug_handle = set_kernel_post_grad_provenance_tracing(
                node_schedule,  # type: ignore[arg-type]
                kernel_name,
            )
            wrapper.write_provenance_debug_handle(kernel_name, debug_handle)