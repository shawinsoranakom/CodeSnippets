def generate_fallback_kernel_with_runtime_lookup(
        self,
        buf_name: str,
        python_kernel_name: str,
        get_args: Callable[[], Sequence[str]],
        op_overload: torch._ops.OpOverload | torch._ops.HigherOrderOperator,
        raw_args: Sequence[Any],
        outputs: Sequence[ir.Buffer],
    ) -> None:
        """Generate a call to a kernel not contained in the C-shim.  This results in
        different code paths for AOT Inductor vs cpp_wrapper Inductor mode."""

        def extract_output_name(
            out: ir.Buffer | Sequence[ir.Buffer] | None,
        ) -> str | None | _OUTPUT_ARGS_TYPE:
            if out is None:
                return None
            if isinstance(out, (ir.MultiOutput, ir._CollectiveKernel)):
                return out.get_name()
            if isinstance(out, ir.MutationOutput):
                mutated_buf_names = out.get_mutation_names()
                assert (
                    isinstance(mutated_buf_names, list) and len(mutated_buf_names) == 1
                ), "Expect only one mutated buffer in MutationOutput"
                return mutated_buf_names[0]
            if isinstance(out, (list, tuple)):
                return [extract_output_name(o) for o in out]  # type: ignore[misc]
            if isinstance(out, int):
                return str(out)
            raise AssertionError(f"Unexpected output: {type(out)}")

        if isinstance(op_overload, torch._ops.HigherOrderOperator):
            assert isinstance(
                op_overload, torch._higher_order_ops.torchbind.CallTorchBind
            ), type(op_overload)
            assert len(raw_args) > 1
            obj = raw_args[0]
            method = raw_args[1]
            return_schema = op_overload.schema(obj, method).returns
        else:
            return_schema = op_overload._schema.returns

        # output_args has the same pytree structure as outputs
        if not return_schema:
            # kernel does not return a value
            output_args: _OUTPUT_ARGS_TYPE = []
        elif isinstance(output_name := extract_output_name(outputs), str):
            output_args = [output_name]
        else:
            # If the schema indicates a return value, we should have a non-None value by
            # this point.
            assert isinstance(output_name, list), type(output_name)
            output_args = output_name

        # In AOT mode, we use a ProxyExecutor to run fallback kernels.
        if V.graph.aot_mode:
            self.generate_fallback_kernel_with_runtime_lookup_aot(
                op_overload,
                raw_args,
                output_args,
                outputs,
            )
            return

        assert isinstance(op_overload, torch._ops.OpOverload), type(op_overload)
        for output in output_args:
            assert output is None or isinstance(output, str), (
                "fallback kernels with runtime lookup currently only support tensor "
                "returns, not more complicated types (such as list-of-list-of-tensor)"
            )

        # In non-AOT mode, we use aoti_torch_call_dispatcher if all the inputs and
        # outputs of the op can be represented with StableIValue.  This avoids the
        # overhead of calling back into Python, and covers most remaining fallback ops.
        if self._compatible_with_stableivalue(op_overload):
            self.generate_fallback_kernel_with_runtime_lookup_nopython(
                get_args,
                op_overload,
                output_args,  # type: ignore[arg-type]
                outputs,
            )
            return

        # Otherwise, we call back into Python, which has some extra runtime overhead,
        # but handles situations like list[Tensor] (currently unrepresentable via
        # StableIValue).
        self.generate_fallback_kernel_with_runtime_lookup_python(
            buf_name,
            python_kernel_name,
            op_overload,
            raw_args,
            output_args,  # type: ignore[arg-type]
            outputs,
        )