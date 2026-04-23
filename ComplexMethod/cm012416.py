def write_wrapper_decl(self):
        """Declare the generated AOTI wrapper entry points."""
        inputs_len = len(V.graph.graph_inputs.keys())
        if V.graph.aot_mode:
            if (
                config.aot_inductor.use_minimal_arrayref_interface
                and not V.graph.is_const_graph
            ):
                input_cpp_types = ", ".join(
                    f"{CppWrapperCpuArrayRef.get_input_cpp_type(x)}"
                    for x in V.graph.graph_inputs.values()
                )
                output_arrayref_types = ", ".join(
                    f"ArrayRefTensor<{DTYPE_TO_CPP[x.get_dtype()]}>"
                    for x in V.graph.graph_outputs
                )

                self.prefix.splice(
                    f"""
                    using AOTInductorModelInputs = std::tuple<{input_cpp_types}>;
                    using AOTInductorModelOutputs = std::tuple<{output_arrayref_types}>;
                    """
                )

            if V.graph.const_module:
                self.header.splice(V.graph.const_module.wrapper_code.header)

                assert V.graph.const_wrapper_code is not None
                self.prefix.splice(V.graph.const_wrapper_code)

                assert V.graph.const_kernel_code is not None
                self.kernel_declarations.splice(V.graph.const_kernel_code)

            if V.graph.is_const_graph:
                self.prefix.splice(
                    """
                    void AOTInductorModel::_const_run_impl(
                        std::vector<AtenTensorHandle>& output_handles,
                        DeviceStreamType stream,
                        AOTIProxyExecutorHandle proxy_executor
                    ) {
                    """
                )
            else:
                if not config.aot_inductor.use_runtime_constant_folding:
                    # If we do not split the constant graph, we'll just create
                    # an empty implementation when wrapping the main module.
                    self.prefix.splice(
                        """
                        void AOTInductorModel::_const_run_impl(
                            std::vector<AtenTensorHandle>& output_handles,
                            DeviceStreamType stream,
                            AOTIProxyExecutorHandle proxy_executor
                        ) {}

                        """
                    )

                run_impl_proto = """
                    void AOTInductorModel::run_impl(
                        AtenTensorHandle*
                            input_handles, // array of input AtenTensorHandle; handles
                                            // are stolen; the array itself is borrowed
                        AtenTensorHandle*
                            output_handles, // array for writing output AtenTensorHandle; handles
                                            // will be stolen by the caller; the array itself is
                                            // borrowed
                        DeviceStreamType stream,
                        AOTIProxyExecutorHandle proxy_executor
                    ) {
                    """

                self.generate_input_output_runtime_checks()
                run_impl_proto += """
                    __check_inputs_outputs(input_handles, output_handles);
                """

                if config.aot_inductor.use_minimal_arrayref_interface:
                    self.prefix.splice(
                        """
                        template <>
                        AOTInductorModelOutputs AOTInductorModel::run_impl_minimal_arrayref_interface<
                          AOTInductorModelInputs, AOTInductorModelOutputs>(
                            const AOTInductorModelInputs& inputs,
                            DeviceStreamType stream,
                            AOTIProxyExecutorHandle proxy_executor
                        ) {
                        """
                    )
                    self.suffix.splice(run_impl_proto)
                    self.suffix.splice(
                        """
                            AOTInductorModelInputs inputs;
                            convert_handles_to_inputs(input_handles, inputs);
                            auto outputs = run_impl_minimal_arrayref_interface<AOTInductorModelInputs, AOTInductorModelOutputs>(
                                inputs, stream, proxy_executor);
                            // NOTE: outputs is full of ArrayRef to thread_local storage. If in the future we need this
                            // interface to perform well for a DSO using the minimal arrayref interface, all we need
                            // to do is provide ThreadLocalCachedTensor for each one!
                            convert_outputs_to_handles(outputs, output_handles);
                        }
                    """
                    )

                    self.suffix.splice(
                        """
                        extern "C" AOTIRuntimeError AOTInductorModelRunMinimalArrayrefInterface(
                            AOTInductorModelHandle model_handle,
                            const AOTInductorModelInputs& inputs,
                            AOTInductorModelOutputs& outputs) {
                          auto model = reinterpret_cast<torch::aot_inductor::AOTInductorModel*>(model_handle);
                          CONVERT_EXCEPTION_TO_ERROR_CODE({
                              outputs = model->run_impl_minimal_arrayref_interface<AOTInductorModelInputs, AOTInductorModelOutputs>(
                                  inputs,
                                  (torch::aot_inductor::DeviceStreamType)nullptr,
                                  nullptr);
                          })
                        }
                    """
                    )

                    self.suffix.splice(
                        f"""
                        // C-ABI-safe variant: uses flat AOTInductorArrayRefTensor arrays
                        // instead of std::tuple across the DSO boundary, and
                        // runs directly on the descriptor arrays to avoid
                        // DSO-side tuple marshaling.
                        extern "C" AOTIRuntimeError AOTInductorModelRunMinimalArrayrefInterfaceV2(
                            AOTInductorModelHandle model_handle,
                            int32_t num_inputs,
                            const AOTInductorArrayRefTensor* c_inputs,
                            int32_t num_outputs,
                            AOTInductorArrayRefTensor* c_outputs) {{
                          constexpr int32_t expected_num_inputs = {len(V.graph.graph_inputs)};
                          constexpr int32_t expected_num_outputs = {len(V.graph.graph_outputs)};
                          auto model = reinterpret_cast<torch::aot_inductor::AOTInductorModel*>(model_handle);
                          CONVERT_EXCEPTION_TO_ERROR_CODE({{
                              if (num_inputs != expected_num_inputs) {{
                                throw std::runtime_error(
                                    std::string("AOTInductorModelRunMinimalArrayrefInterfaceV2 expected ")
                                    + std::to_string(expected_num_inputs)
                                    + " inputs but got "
                                    + std::to_string(num_inputs));
                              }}
                              if (num_outputs != expected_num_outputs) {{
                                throw std::runtime_error(
                                    std::string("AOTInductorModelRunMinimalArrayrefInterfaceV2 expected ")
                                    + std::to_string(expected_num_outputs)
                                    + " outputs but got "
                                    + std::to_string(num_outputs));
                              }}
                              if (num_inputs > 0 && c_inputs == nullptr) {{
                                throw std::runtime_error(
                                    "AOTInductorModelRunMinimalArrayrefInterfaceV2 received null input descriptors");
                              }}
                              if (num_outputs > 0 && c_outputs == nullptr) {{
                                throw std::runtime_error(
                                    "AOTInductorModelRunMinimalArrayrefInterfaceV2 received null output descriptors");
                              }}
                              model->run_impl_minimal_arrayref_interface_v2_raw(
                                  c_inputs,
                                  c_outputs,
                                  (torch::aot_inductor::DeviceStreamType)nullptr,
                                  nullptr);
                          }})
                        }}
                    """
                    )
                else:
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
            if not config.aot_inductor.use_minimal_arrayref_interface:
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
                    if config.aot_inductor.use_minimal_arrayref_interface:
                        self.prefix.writeline(
                            f"auto {input_key} = std::get<{idx}>(inputs);"
                        )
                        continue
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

            assert all(
                isinstance(v, torch.Tensor) for v in list(V.graph.constants.values())
            ), "Expect all constants to be Tensor"
            for idx, constants_key in enumerate(V.graph.constants.keys()):
                if V.graph.aot_mode:
                    # Weights are stored in constants_ and owned by RAIIAtenTensorHandle there.
                    # Don't call std::move here because it will cause constants_ to lose the ownership.
                    self.prefix.writeline(
                        f"""auto {constants_key} = constants_->at({idx});"""
                    )
                else:
                    # Append constants as inputs to the graph
                    constants_idx = inputs_len + idx
                    self.prefix.writeline(
                        f"auto {constants_key} = std::move(inputs[{constants_idx}]);"
                    )

            self.codegen_inputs()

            if V.graph.aot_mode:
                if not V.graph.is_const_graph:
                    if config.aot_inductor.use_minimal_arrayref_interface:
                        # TODO: input shape checking for regular tensor interface as well?
                        self.codegen_input_numel_asserts()
                    else:
                        self.prefix.writeline("inputs.clear();")
                self.prefix.writeline(
                    "[[maybe_unused]] auto& kernels = static_cast<AOTInductorModelKernels&>(*this->kernels_.get());"
                )