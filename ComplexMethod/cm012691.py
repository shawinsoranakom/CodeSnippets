def generate_end(self, result):
        """Generates the end of the code block, and any code needed to call it."""
        if V.graph.aot_mode:
            if V.graph.is_const_graph:
                result.writeline(f"}} // {self.aoti_model_class_name}::_const_run_impl")
            else:
                result.writeline("} // namespace torch::aot_inductor\n\n\n")
            return

        if config.cpp_wrapper_build_separate:
            # Close the wrapper code block, then write any kernel definitions.
            result.splice('"""\n)')
            if self.kernel_declarations:
                result.splice('\nkernel_src = (\nr"""')
                result.splice(self.kernel_declarations.getvalue())
                result.splice('"""\n)')
            else:
                result.splice(
                    """
                    kernel_src = ''
                    """
                )
        else:
            # Merge main code and kernel code
            result.splice(self.kernel_declarations.getvalue())
            self.kernel_declarations.clear()
            # Close the wrapper code block
            result.splice('"""\n)')

        kernel_code = "kernel_src" if config.cpp_wrapper_build_separate else "None"
        # Cpp entry function for JIT with cpp wrapper
        result.splice(
            f"""
            inductor_entry = CppWrapperCodeCache.load_pybinding(
                argtypes=["std::vector<AtenTensorHandle>"],
                main_code=cpp_wrapper_src,
                device_type="{self.device}",
                num_outputs={len(V.graph.graph_outputs)},
                kernel_code={kernel_code},
            )
            """
        )

        wrapper_body = "input_tensors = [arg if isinstance(arg, torch.Tensor) else torch.tensor(arg, device='cpu') for arg in args]"
        if V.graph.constants:
            # Append constants to the input args for cpp wrapper.
            # Python wrapper directly gets the value inside the wrapper call
            # as a global variable passed when calling exec(code, mod.__dict__, mod.__dict__).
            # For cpp wrapper, we need to pass this python value to the inductor_entry_impl function explicitly.
            assert all(
                isinstance(v, torch.Tensor) for v in list(V.graph.constants.values())
            ), "Expect all constants to be Tensor"
            constants_str = f"[{', '.join(V.graph.constants.keys())}]"
            wrapper_body += f"""
                    constants_tensor = {constants_str}
                    input_tensors.extend(constants_tensor)
            """
        # Convert vector of at::Tensor to vector of AtenTensorHandle.
        # If we pass at::Tensor, the compilation will be too slow.
        wrapper_body += """
                    input_handles = torch._C._aoti.unsafe_alloc_void_ptrs_from_tensors(input_tensors)
        """
        # Release the inputs for memory reuse.
        wrapper_body += """
                    args.clear()
                    del input_tensors
        """

        # unwrap output tensor back to python scalar
        if all(x for x in self.output_is_tensor.values()):
            # If no ShapeAsConstantBuffer in the output, directly return the output as tensors
            outputs_str = "output_tensors"
        else:
            outputs = [
                (
                    f"output_tensors[{i}]"
                    if self.output_is_tensor[i]
                    else f"output_tensors[{i}].item()"
                )
                for i in range(len(V.graph.graph_outputs))
            ]
            outputs_str = f"[{', '.join(outputs)}]"
        wrapper_body += f"""
                    output_handles = f(input_handles)
                    output_tensors = torch._C._aoti.alloc_tensors_by_stealing_from_void_ptrs(output_handles)
                    return {outputs_str}
        """

        # Wrap the func to support setting result._boxed_call = True
        result.splice(
            f"""
            def _wrap_func(f):
                def g(args):
                    {wrapper_body}
                return g

            call = _wrap_func(inductor_entry)
            """
        )