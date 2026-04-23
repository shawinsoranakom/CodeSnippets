def _codegen_v2_raw_outputs(
        self, code: IndentedBuffer, output_refs: list[str]
    ) -> None:
        cst_names = V.graph.constants.keys()

        def write_output_to_c_array(idx: int, output: str) -> None:
            output_arrayref_name = f"output_arrayref_{idx}"
            code.splice(
                f"""
                std::tuple_element_t<{idx}, AOTInductorModelOutputs> {output_arrayref_name};
                convert_handle_to_arrayref_tensor({output}, {output_arrayref_name});
                torch::aot_inductor::arrayref_tensor_to_c({output_arrayref_name}, c_outputs[{idx}]);
                """
            )

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
                output_tensor = f"scalar_to_tensor_{next(self.scalar_to_tensor_id)}"
                code.writeline(
                    f"RAIIAtenTensorHandle {output_tensor} = scalar_to_tensor_handle({output});"
                )
                write_output_to_c_array(idx, output_tensor)
                continue

            output_is_tensor_handle_expr = (
                f"std::is_same_v<std::decay_t<decltype({output})>,"
                "RAIIAtenTensorHandle> || "
                f"std::is_same_v<std::decay_t<decltype({output})>,"
                "AtenTensorHandle> || "
                f"std::is_same_v<std::decay_t<decltype({output})>,"
                "ConstantHandle>"
            )
            code.writeline(f"if constexpr ({output_is_tensor_handle_expr}) {{")
            with code.indent():
                cached_output_name = f"cached_output_{next(self.cached_output_id)}"
                code.writeline(
                    f"thread_local RAIIAtenTensorHandle {cached_output_name};"
                )
                if is_constant_buffer:
                    code.splice(
                        f"""
                        AtenTensorHandle {cached_output_name}_tmp;
                        aoti_torch_clone({output}, &{cached_output_name}_tmp);
                        {cached_output_name} = {cached_output_name}_tmp;
                        """
                    )
                else:
                    code.writeline(f"{cached_output_name} = {output}.release();")
                write_output_to_c_array(idx, cached_output_name)
            code.writeline("} else {")
            with code.indent():
                cached_output_name = f"cached_output_{next(self.cached_output_id)}"
                output_arrayref_type = f"output_arrayref_{idx}_type"
                output_element_type = f"output_arrayref_{idx}_element_type"
                output_arrayref_name = f"output_arrayref_{idx}"
                code.splice(
                    f"""
                    thread_local ThreadLocalCachedOutputArray<std::decay_t<decltype({output})>>
                        {cached_output_name}({output});
                    {cached_output_name}.copy_data_from({output});
                    using {output_arrayref_type} = std::tuple_element_t<{idx}, AOTInductorModelOutputs>;
                    using {output_element_type} = typename {output_arrayref_type}::value_type;
                    auto {output_arrayref_name} = {cached_output_name}.arrayref_tensor<{output_element_type}>();
                    torch::aot_inductor::arrayref_tensor_to_c({output_arrayref_name}, c_outputs[{idx}]);
                    """
                )
            code.writeline("}")