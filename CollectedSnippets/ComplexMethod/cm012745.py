def render(  # type: ignore[override]
        self,
        kernel: CUTLASSTemplateKernel,
        op: "cutlass_gemm_op.GemmOperation" = None,  # type: ignore[name-defined]  # noqa: F821
        template_buffer_node: CUTLASSTemplateBuffer | None = None,
        epilogue_nodes: list[BaseSchedulerNode] | None = None,
        **kwargs,
    ) -> str:
        """
        The primary entry point for the code rendering process used in this template.
        Renders the Cutlass based CUDA/XPU C++ code for the GEMM Kernel that this template is designed to implement,
        including potentially fused epilogues.

        Args:
            kernel (CUTLASSTemplateKernel): The kernel to be rendered.
            op (cutlass_gemm_op.GemmOperation, optional): A GEMM operation that is required to be compatible with the
                input and output definitions as well as a possible epilogue. Defaults to None.
            **kwargs: Additional keyword arguments. Currently unused.

        Returns:
            str: Cutlass based CUDA/XPU C++ code fragment as a string, to be used by the current
            CUTLASSTemplateKernel or autotuning code.

        Note:
            All inputs and their corresponding buffer addresses and names take precedence over previously
            passed inputs to the template at construction time. However, they should be layout compatible.
        """
        assert cutlass_utils.try_import_cutlass()
        import cutlass_library.gemm_operation as cutlass_gemm_op
        import cutlass_library.library as cutlass_lib

        assert isinstance(op, cutlass_gemm_op.GemmOperation), (
            "op argument is required and has to be an instance of GemmOperation"
        )

        if epilogue_nodes:
            if self.device_type == "cuda" and not self._has_tma_epilogue(op):
                raise NotImplementedError(
                    "Non-TMA epilogue visitor tree is not supported in NV-Cutlass."
                )

        assert len(self.input_nodes) >= 2 and self.output_node is not None
        X, W = self.input_nodes[0], self.input_nodes[1]
        for input_node in self.input_nodes:
            if not isinstance(X.layout, FixedLayout):
                input_node.freeze_layout()

        Y = self.output_node
        if template_buffer_node is not None:
            Y = template_buffer_node

        Bias, extra_inputs, extra_names = self._get_extra_inputs_and_names(op)

        # Define Kernel call signature
        # Important: This step also populates Kernel name to node mapping data structures,
        # which are required further below ( for example by the template renderer )
        inputs = [X, W, Bias, *extra_inputs]
        names = ["X", "W", "Bias", *extra_names] + ["Y"]
        names_str = ",".join(names)
        if self.input_reorder is not None:
            input_reorder = self.input_reorder
        else:
            input_reorder = None

        # The layouts might have changed between autotuning and this call if they were FlexibleLayout
        # we need to adapt, which might lead to suboptimal performance.
        op = self.fix_op_layout(op, X, W, Bias, Y)

        # to make op mutable without affecting others
        op = copy.deepcopy(op)
        is_scaled_mm = len(self.input_nodes) in (4, 5)
        if Bias is not None and not is_scaled_mm:
            assert Bias.get_dtype() == X.get_dtype()
            # This might have been set to void during filtering, when the assumption was still that there's no C
            # operand
            op.C.element = op.A.element

            assert op.C.element == op.D.element, (
                f"Expect C and D to have the same dtype, found {op.C.element} and {op.D.element}"
            )

        argument_template, epilogue_template = self._get_template_args(op)
        should_swap_xw: bool = False
        if Bias is not None and self._has_tma_epilogue(op):
            if (
                op.epilogue_schedule
                != cutlass_lib.EpilogueScheduleType.EpilogueTransposed
                and self.should_swap_XW(Bias)
            ):
                # TMA epilogue requires bias vector in column major to get best perf.
                op = self.swap_XW(op)
                should_swap_xw = True

        name_to_buffer = {node.get_name(): node for node in self.input_nodes}
        # handle the fake output buffer during lowering
        name_to_buffer[Y.get_name()] = Y  # type: ignore[assignment]

        if epilogue_nodes or is_scaled_mm:
            if epilogue_nodes:
                (
                    input_names,
                    output_names,
                    var_name_to_buffer_name,
                    evt_py_code,
                ) = CutlassEVTCodegen.ir_to_evt_python_code(
                    Y.get_name(), epilogue_nodes, V.kernel.removed_buffers
                )

                # TODO: mlazos remove this by returning buffer metadata from
                # ir_to_evt_python code
                for name, buf in (
                    V.graph.name_to_buffer | V.graph.graph_inputs
                ).items():
                    if name not in name_to_buffer:
                        name_to_buffer[name] = buf  # type: ignore[assignment]

                D_output_name = var_name_to_buffer_name["D"]
                D_output_buffer = name_to_buffer[D_output_name]
                Y = D_output_buffer  # type: ignore[assignment]
                # Interestingly, I don't think the rest of the layout matters here since we
                # use the properties of the Y buffer to fill in D's properties in the epilogue
                # args. This is needed though because it defines types expected in the epilogue args.
                op.D.element = cutlass_utils.torch_dtype_to_cutlass_type(
                    D_output_buffer.get_dtype()
                )

                assert output_names, "There should be at least one write"

                epilogue_inputs = [name_to_buffer[name] for name in input_names]
                outputs = [name_to_buffer[name] for name in output_names]
            else:  # Scaled MM, we read the two scale matrices (and optional bias) and write a single output
                bias = None if len(self.input_nodes) < 5 else self.input_nodes[4]
                bias_name = bias.get_name() if bias else None

                (
                    evt_read_names,
                    var_name_to_buffer_name,
                    evt_py_code,
                ) = scaled_mm_evt(
                    self.input_nodes[2].get_name(),  # scale_A
                    self.input_nodes[3].get_name(),  # scale_B
                    bias_name,
                    Y.get_name(),
                )

                input_names = list(evt_read_names)
                output_names = []  # We only need Y
                epilogue_inputs = [self.input_nodes[2], self.input_nodes[3]]
                if bias:
                    epilogue_inputs.append(bias)
                outputs = []

            acc_dtype = cutlass_utils.get_accumulator_dtype(
                [X.get_dtype(), W.get_dtype()]
            )
            assert acc_dtype, "Could not determine accumulator dtype"

            evt_name, evt_args, evt_code, evt_arg_renames = self._render_evt(
                op,
                evt_py_code,
                var_name_to_buffer_name,
                name_to_buffer,
                Y.get_dtype(),
                acc_dtype,
            )

            inputs = [
                X,
                W,
                Bias,
                *epilogue_inputs,  # type: ignore[list-item]
                Y,
                *extra_inputs,
            ]
            input_names = [evt_arg_renames.get(name) for name in input_names]
            output_names = [evt_arg_renames.get(name) for name in output_names]

            names_str = ",".join(
                ["X", "W", "Bias", *input_names, "Y", *output_names, *extra_names]
            )
        else:
            evt_name = None
            outputs = [Y]
            evt_args = f"{{ElementComputeEpilogue({self.alpha}), ElementComputeEpilogue({self.beta})}}"
            evt_code = ""

        kernel_call_signature = kernel.def_kernel(
            inputs=inputs,  # type: ignore[arg-type]
            outputs=outputs,  # type: ignore[arg-type]
            names_str=names_str,
            input_reorder=input_reorder,
        )

        test_call_statement = self.test_call_statement(kernel, inputs, names_str)

        instance_definition, instance_type = self._define_gemm_instance(op, evt_name)
        dynamic_cluster = self._dynamic_cluster_block(op)

        options = {
            "alpha": self.alpha,
            "beta": self.beta,
            "X": X,
            "W": W,
            "Y": Y,
            "kernel_call_signature": kernel_call_signature,
            "Bias": Bias,
            "epilogue_template": epilogue_template,
            "argument_template": argument_template,
            "should_swap_xw": should_swap_xw,
            "template": self,
            "kernel": kernel,
            "instance_definition": instance_definition,
            "instance_type": instance_type,
            "input_reorder": self.input_reorder,
            "epilogue_args": evt_args,
            "test_call_statement": test_call_statement,
            "op_conf_name": op.configuration_name(),
            "epilogue_visitor_tree": evt_code,
            "dynamic_cluster": dynamic_cluster,
        }
        options.update(dict(zip(extra_names, extra_inputs)))
        res = self._template_from_string(self._get_template()).render(**options)
        if inductor_cutlass_config.generate_test_runner and not is_dynamic(
            X, W, Y, Bias
        ):
            test_runner_code = self._template_from_string(
                GEMM_STANDALONE_RUNNER_TEMPLATE
            ).render(**options)
            res += "\n\n" + test_runner_code

        # splice to remove trailing spaces in each line
        buf = IndentedBuffer()
        buf.splice(res)
        return buf.getvalue()