def codegen_template(
        self,
        template_node: BaseSchedulerNode,
        epilogue_nodes: Sequence[BaseSchedulerNode],
        prologue_nodes: Sequence[BaseSchedulerNode],
    ) -> str | None:
        if self._cutlass_scheduling.is_cutlass_template(template_node):
            assert not prologue_nodes
            return self._cutlass_scheduling.codegen_template(
                template_node, epilogue_nodes, prologue_nodes
            )
        elif self._rocm_cpp_scheduling.is_rocm_cpp_template(template_node):
            assert not epilogue_nodes
            assert not prologue_nodes
            return self._rocm_cpp_scheduling.codegen_template(
                template_node, epilogue_nodes, prologue_nodes
            )
        elif self._cutedsl_scheduling.is_cutedsl_template(template_node):
            # TODO remove this when we add epilogue support
            assert not epilogue_nodes
            assert not prologue_nodes
            return self._cutedsl_scheduling.codegen_template(
                template_node, epilogue_nodes, prologue_nodes
            )
        elif self._nv_universal_gemm_scheduling.is_nv_universal_gemm_template(
            template_node
        ):
            # NVIDIA Universal GEMM doesn't support epilogue/prologue fusion yet
            assert not epilogue_nodes
            assert not prologue_nodes
            return self._nv_universal_gemm_scheduling.codegen_template(
                template_node, epilogue_nodes, prologue_nodes
            )
        else:
            return self._triton_scheduling.codegen_template(
                template_node, epilogue_nodes, prologue_nodes
            )