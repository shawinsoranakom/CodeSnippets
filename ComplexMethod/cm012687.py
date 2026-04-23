def write_wrapper_decl(self):
        inputs_len = len(V.graph.graph_inputs.keys())
        if V.graph.aot_mode:
            self.codegen_additional_funcs()

            if V.graph.const_module:
                self.header.splice(V.graph.const_module.wrapper_code.header)

                assert V.graph.const_wrapper_code is not None
                self.prefix.splice(V.graph.const_wrapper_code)

                assert V.graph.const_kernel_code is not None
                self.kernel_declarations.splice(V.graph.const_kernel_code)

            if V.graph.is_const_graph:
                self.prefix.splice(
                    f"""
                    void {self.aoti_model_class_name}::_const_run_impl(
                        std::vector<AtenTensorHandle>& output_handles,
                        DeviceStreamType stream,
                        AOTIProxyExecutorHandle proxy_executor
                    ) {{
                    """
                )
            else:
                if not config.aot_inductor.use_runtime_constant_folding:
                    # If we do not split the constant graph, we'll just create
                    # an empty implementation when wrapping the main module.
                    self.prefix.splice(
                        f"""
                        void {self.aoti_model_class_name}::_const_run_impl(
                            std::vector<AtenTensorHandle>& output_handles,
                            DeviceStreamType stream,
                            AOTIProxyExecutorHandle proxy_executor
                        ) {{}}

                        """
                    )

                run_impl_proto = f"""
                    void {self.aoti_model_class_name}::run_impl(
                        AtenTensorHandle*
                            input_handles, // array of input AtenTensorHandle; handles
                                            // are stolen; the array itself is borrowed
                        AtenTensorHandle*
                            output_handles, // array for writing output AtenTensorHandle; handles
                                            // will be stolen by the caller; the array itself is
                                            // borrowed
                        DeviceStreamType stream,
                        AOTIProxyExecutorHandle proxy_executor
                    ) {{
                        __check_inputs_outputs(input_handles, output_handles);
                    """

                self.generate_input_output_runtime_checks()
                self.prefix.splice(run_impl_proto)
        else:
            # cpp entry function for JIT with cpp wrapper
            self.prefix.splice(
                """
                void inductor_entry_impl(
                    AtenTensorHandle*
                        input_handles, // array of input AtenTensorHandle; handles
                                        // are stolen; the array itself is borrowed
                    AtenTensorHandle*
                        output_handles  // array for writing output AtenTensorHandle; handles
                                        // will be stolen by the caller; the array itself is
                                        // borrowed)
                ) {
                """
            )
        with self.prefix.indent():
            # assign inputs and outputs in both cases so the later codegen can be simplified
            if not V.graph.is_const_graph:
                if V.graph.aot_mode:
                    num_args = len(V.graph.graph_inputs)
                else:
                    # Weights are promoted in the JIT mode
                    num_args = len(V.graph.graph_inputs) + len(V.graph.constants)
                    # release GIL to support multiple instances inference (in different threads of the same process)
                    self.prefix.splice("py::gil_scoped_release_simple release;")

                self.prefix.splice(
                    f"""
                        auto inputs = steal_from_raw_handles_to_raii_handles(input_handles, {num_args});
                    """
                )

            if inputs_len != 0:
                for idx, input_key in enumerate(V.graph.graph_inputs.keys()):
                    # unwrap input tensor back to scalar
                    if isinstance(V.graph.graph_inputs[input_key], sympy.Expr):
                        from ..graph import may_get_constant_buffer_dtype

                        dtype = may_get_constant_buffer_dtype(
                            V.graph.graph_inputs[input_key]  # type: ignore[arg-type]
                        )
                        assert dtype is not None, (
                            "Fails to get the dtype of the sympy.Expr"
                        )
                        self.codegen_tensor_item(
                            dtype, f"inputs[{idx}]", input_key, self.prefix
                        )
                    else:
                        self.prefix.writeline(
                            f"auto {input_key} = std::move(inputs[{idx}]);"
                        )
                # debug printing for all input args to AOTI model
                debug_printer_manager = V.graph.wrapper_code.debug_printer
                debug_printer_manager.codegen_model_inputs_value_print(
                    input_args_to_print=[
                        input_key
                        for input_key in V.graph.graph_inputs
                        if input_key.startswith("arg")
                    ]
                )

            assert all(
                isinstance(v, torch.Tensor) for v in list(V.graph.constants.values())
            ), "Expect all constants to be Tensor"
            for idx, constants_key in enumerate(V.graph.constants.keys()):
                if V.graph.aot_mode:
                    # Weights are stored in constants_ and owned by ConstantHandle there.
                    # Don't call std::move here because it will cause constants_ to lose the ownership.
                    self.prefix.writeline(
                        f"""[[maybe_unused]] auto& {constants_key} = constants_->at({idx});"""
                    )
                else:
                    # Append constants as inputs to the graph
                    constants_idx = inputs_len + idx
                    self.prefix.writeline(
                        f"[[maybe_unused]] auto {constants_key} = std::move(inputs[{constants_idx}]);"
                    )

            self.codegen_inputs()

            if V.graph.aot_mode:
                if not V.graph.is_const_graph:
                    self.prefix.writeline("inputs.clear();")
                self.prefix.writeline(
                    "[[maybe_unused]] auto& kernels = static_cast<AOTInductorModelKernels&>(*this->kernels_.get());"
                )