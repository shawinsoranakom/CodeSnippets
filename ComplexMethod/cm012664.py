def codegen_template(
        self,
        template_node,
        epilogue_nodes,
        prologue_nodes,
        *,
        only_gen_src_code=False,
        hint_override: int | None = None,
    ) -> str | None:
        """
        Codegen a triton template with multi-kernel dispatch support

        If `only_gen_src_code=True` the src code will be returned instead of being
        codegenned into the wrapper
        """

        _, (_numel, rnumel) = template_node.group
        assert rnumel == 1

        if (
            isinstance(template_node.node, MultiTemplateBuffer)
            and template_node.node._make_kernel_renders
            and len(template_node.node._make_kernel_renders) > 1
            and self._kernel_has_dynamic_shapes(template_node.node)
        ):
            kernels = {}
            src_codes = []

            for (
                size_hint,
                make_kernel_render,
            ) in template_node.node._make_kernel_renders.items():
                kernel, render = make_kernel_render(
                    template_node.node, hint_override=hint_override
                )

                if only_gen_src_code:
                    src_code = self._codegen_single_template(
                        kernel,
                        render,
                        template_node,
                        epilogue_nodes,
                        prologue_nodes,
                        only_gen_src_code=True,
                    )
                    assert isinstance(src_code, str)
                    # pyrefly: ignore [bad-argument-type]
                    src_codes.append(src_code)
                else:
                    if size_hint is None:
                        continue  # skip kernel generation based on real runtime value; only use hints
                    kernel = self._codegen_single_template(
                        kernel,
                        render,
                        template_node,
                        epilogue_nodes,
                        prologue_nodes,
                        only_gen_src_code=False,
                    )
                    shape_cache_key = (
                        None
                        if size_hint is None
                        else self._make_shape_cache_key(template_node.node, size_hint)
                    )
                    # pyrefly: ignore [unsupported-operation]
                    kernels[shape_cache_key] = kernel

            if only_gen_src_code:
                return "\n\n".join(src_codes)

            MultiKernel.merge_workspaces_inplace(list(kernels.values()))
            multi_kernel = SizeHintMultiKernel(kernels)
            node_schedule = [*prologue_nodes, template_node, *epilogue_nodes]
            self.codegen_comment(node_schedule, multi_kernel.kernel_name)
            multi_kernel.call_kernel(multi_kernel.kernel_name)
            V.graph.removed_buffers |= multi_kernel.removed_buffers
            V.graph.inplaced_to_remove |= multi_kernel.inplaced_to_remove
            self.free_buffers_in_scheduler()
            return None
        else:
            kernel, render = template_node.node.make_kernel_render(
                template_node.node, hint_override=hint_override
            )

            if only_gen_src_code:
                return self._codegen_single_template(
                    kernel,
                    render,
                    template_node,
                    epilogue_nodes,
                    prologue_nodes,
                    only_gen_src_code=True,
                )
            else:
                kernel = self._codegen_single_template(
                    kernel,
                    render,
                    template_node,
                    epilogue_nodes,
                    prologue_nodes,
                    only_gen_src_code=False,
                )

                node_schedule = [*prologue_nodes, template_node, *epilogue_nodes]
                self.codegen_comment(node_schedule, kernel.kernel_name)
                kernel.call_kernel(kernel.kernel_name, template_node.node)

                V.graph.removed_buffers |= kernel.removed_buffers
                V.graph.inplaced_to_remove |= kernel.inplaced_to_remove
                self.free_buffers_in_scheduler()
                return None