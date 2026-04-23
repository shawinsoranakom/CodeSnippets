def generate_return(self, output_refs: list[str]):
        cst_names = V.graph.constants.keys()
        arr_iface = (
            not V.graph.is_const_graph
            and config.aot_inductor.use_minimal_arrayref_interface
        )  # For brevity.

        if arr_iface and V.graph.aot_mode:
            self.v2_raw_wrapper_body.clear()
            self.v2_raw_wrapper_body.splice(self.wrapper_call)
            self.v2_raw_output_refs = list(output_refs)

        def use_thread_local_cached_output_tensor(idx, output):
            cached_output_name = f"cached_output_{next(self.cached_output_id)}"
            cache_type = "Array" if arr_iface else "Tensor"
            self.wrapper_call.writeline(
                f"thread_local ThreadLocalCachedOutput{cache_type}<std::decay_t<decltype({output})>> "
                f"{cached_output_name}({output});"
            )
            if arr_iface:
                self.wrapper_call.writeline(
                    f"{cached_output_name}.copy_data_from({output});"
                )
                output_entry = f"std::get<{idx}>(output_arrayref_tensors)"
                element_type = f"std::decay_t<decltype({output_entry}.data()[0])>"
                self.wrapper_call.writeline(
                    f"{output_entry} = {cached_output_name}.arrayref_tensor<{element_type}>();"
                )
            else:
                self.wrapper_call.writeline(
                    f"{cached_output_name}.copy_data_from({output});"
                )
                self.wrapper_call.writeline(
                    f"AOTI_TORCH_ERROR_CODE_CHECK(aoti_torch_new_uninitialized_tensor(&output_handles[{idx}]));"
                )
                self.wrapper_call.writeline(
                    f"AOTI_TORCH_ERROR_CODE_CHECK(aoti_torch_assign_tensors({cached_output_name}.tensor(), "
                    f"output_handles[{idx}]));"
                )

        if arr_iface:
            self.wrapper_call.writeline(
                "AOTInductorModelOutputs output_arrayref_tensors;"
            )

        output2idx: dict[str, int] = {}
        for idx, output in enumerate(output_refs):
            if output == "nullptr":
                continue

            is_constant_buffer = output in cst_names
            output_buffer = V.graph.graph_outputs[idx]
            if isinstance(output_buffer, ir.BaseView):
                output_storage = output_buffer.unwrap_view()
                assert isinstance(output_storage, (ir.BaseView, ir.MutableBox))
                if isinstance(output_storage.data, ir.ConstantBuffer):
                    is_constant_buffer = True

            if isinstance(output_buffer, ir.ShapeAsConstantBuffer):
                # Need to wrap scalar into tensor as the main function returns a vector of tensors
                output_tensor = self.codegen_scalar_to_tensor(output)
                self.wrapper_call.writeline(
                    f"output_handles[{idx}] = {output_tensor}.release();"
                )
                continue

            output_is_tensor_handle_expr = (
                f"std::is_same_v<std::decay_t<decltype({output})>,"
                "RAIIAtenTensorHandle> || "
                f"std::is_same_v<std::decay_t<decltype({output})>,"
                "AtenTensorHandle> || "
                f"std::is_same_v<std::decay_t<decltype({output})>,"
                "ConstantHandle>"
            )
            self.wrapper_call.writeline(
                f"if constexpr ({output_is_tensor_handle_expr}) {{"
            )
            with self.wrapper_call.indent():
                if arr_iface:
                    cached_output_name = f"cached_output_{next(self.cached_output_id)}"
                    self.wrapper_call.writeline(
                        f"thread_local RAIIAtenTensorHandle {cached_output_name};"
                    )
                    if is_constant_buffer:
                        # NOTE(return_constant): In some rare cases where we return
                        # a constant, we have to return a copy of this constant,
                        # because (1) constants are not owned by the Model instance
                        # (2) constants remain the same cross inference runs,
                        # assuming they are not updated at runtime Basically, we
                        # cannot release or transfer the ownership of any original
                        # constant to the user.
                        self.wrapper_call.writeline(
                            f"AtenTensorHandle {cached_output_name}_tmp;"
                        )
                        self.wrapper_call.writeline(
                            f"aoti_torch_clone({output}, &{cached_output_name}_tmp);"
                        )
                        self.wrapper_call.writeline(
                            f"{cached_output_name} = {cached_output_name}_tmp;"
                        )
                    else:
                        self.wrapper_call.writeline(
                            f"{cached_output_name} = {output}.release();"
                        )
                    self.wrapper_call.writeline(
                        f"convert_handle_to_arrayref_tensor({cached_output_name}, "
                        f"std::get<{idx}>(output_arrayref_tensors));"
                    )
                else:
                    if is_constant_buffer:
                        # See NOTE(return_constant) above.
                        self.wrapper_call.writeline(
                            f"aoti_torch_clone({output}, &output_handles[{idx}]);"
                        )
                    else:
                        if output in output2idx:
                            src_idx = output2idx[output]
                            self.wrapper_call.writeline(
                                f"output_handles[{idx}] = output_handles[{src_idx}];"
                            )
                        else:
                            self.wrapper_call.writeline(
                                f"output_handles[{idx}] = {output}.release();"
                            )
            self.wrapper_call.writeline("} else {")
            with self.wrapper_call.indent():
                use_thread_local_cached_output_tensor(idx, output)
            self.wrapper_call.writeline("}")

            if output not in output2idx:
                output2idx[output] = idx
        if arr_iface:
            self.wrapper_call.writeline("return output_arrayref_tensors;")