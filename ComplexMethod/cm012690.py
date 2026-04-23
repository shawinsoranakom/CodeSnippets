def generate_return(self, output_refs: list[str]):
        cst_names = V.graph.constants.keys()
        output2idx: dict[str, int] = {}

        # If any output ref represents an rvalue tensor, materialize it to an lvalue
        # RAIIAtenTensorHandle first.  This prevents situations where the code for the
        # rvalue tensor references tensor handles whose contents are modified below.
        output_refs = [
            self.create_tmp_raii_handle_var_if_needed(o, self.wrapper_call)
            for o in output_refs
        ]

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

            if output not in output2idx:
                output2idx[output] = idx