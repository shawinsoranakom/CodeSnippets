def can_fuse_vertical(
        self, node1: BaseSchedulerNode, node2: BaseSchedulerNode
    ) -> bool:
        if self.is_cutlass_template(node1) and isinstance(node2, BaseSchedulerNode):
            assert node1.node, "node1.node should not be None"
            return self._can_fuse_epilogue_impl(
                cast(CUTLASSTemplateBuffer, node1.node),
                [],
                node2,  # type: ignore[arg-type]
            )
        elif self.is_cutlass_fused_template(node1) and isinstance(
            node2, BaseSchedulerNode
        ):
            assert node1.node, "node1.node should not be None"
            assert node2.node, "node2.node should not be None"
            fnode1 = cast(FusedSchedulerNode, node1)
            return self._can_fuse_epilogue_impl(
                fnode1.get_template_node(),  # type: ignore[arg-type]
                self._unwrap_epilogue_nodes(fnode1),
                node2,  # type: ignore[arg-type]
            )

        return False