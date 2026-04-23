def generate_fallback_kernel_with_runtime_lookup_python(
        self,
        buf_name: str,
        python_kernel_name: str,
        op_overload: torch._ops.OpOverload,
        raw_args: Sequence[Any],
        output_args: Sequence[str | None],
        raw_outputs: Sequence[ir.Buffer],
    ) -> None:
        """Generate fallback kernel calls with runtime (non-AOT) dispatch.  This can
        only be called in cpp_wrapper mode, and assumes that the input is a non-None
        OpOverload.

        This function calls into Python to dispatch, which allows it to handle datatypes
        that cannot be contained in StableIValue, at the cost of some performance."""
        self.load_custom_op_wrapper()

        num_args = len(raw_args)
        py_args_var = f"py_args_{next(self.arg_var_id)}"
        # First arg is always the python op name
        lines = textwrap.dedent(
            f"""
            RAIIPyObject {py_args_var}(PyTuple_New({num_args + 1}));
            if (!{py_args_var}) {{
                throw std::runtime_error("PyTuple_New {py_args_var} failed");
            }}
            PyTuple_SetItem({py_args_var}, 0, PyUnicode_FromString("{python_kernel_name}"));
            """
        )

        for idx, (raw_arg, schema_arg) in enumerate(
            zip(raw_args, op_overload._schema.arguments)
        ):
            lines += self.generate_py_arg(
                py_args_var, idx + 1, raw_arg, schema_arg.real_type
            )

        lines += textwrap.dedent(
            f"""
            // Call the custom op in Python
            RAIIPyObject py_{buf_name}(PyObject_CallObject(custom_op_wrapper, {py_args_var}));
            if (!py_{buf_name}) {{
                if (PyErr_Occurred()) {{
                    return;
                }}
                throw std::runtime_error("PyObject_CallObject {python_kernel_name} failed");
            }}
            """
        )

        if len(output_args) == 1 and (output := output_args[0]) is not None:
            # result is a single tensor
            lines += f"{output} = reinterpret_cast<AtenTensorHandle>(PyCapsule_GetPointer(py_{buf_name}.get(), NULL));\n"
        else:
            # result is a tuple of tensors
            for idx, output_arg in enumerate(output_args):
                if output_arg is None:
                    continue
                lines += f"{output_arg} = reinterpret_cast<AtenTensorHandle>(PyCapsule_GetPointer(PyList_GET_ITEM(py_{buf_name}.get(), {idx}), NULL));\n"

        if raw_outputs:
            declarations_before_scope = [
                f"RAIIAtenTensorHandle {output_arg};"
                for output_arg, raw_output_arg in zip(output_args, raw_outputs)  # type: ignore[arg-type]
                if output_arg is not None
                and not isinstance(raw_output_arg, ir.MutationOutput)
            ]
        else:
            declarations_before_scope = [
                f"RAIIAtenTensorHandle {output_arg};"
                for output_arg in output_args  # type: ignore[arg-type]
                if output_arg is not None
            ]
        scope_gil_acquire = self.generate_scoped_gil_acquire(
            declarations_before_scope, lines
        )
        self.writelines(scope_gil_acquire)