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