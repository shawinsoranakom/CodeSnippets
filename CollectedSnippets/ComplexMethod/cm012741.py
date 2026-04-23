def global_filter_ops(
        cls,
        ops: list["cutlass_library.gemm_op.GemmOperation"],  # type: ignore[name-defined]  # noqa: F821
    ) -> list["cutlass_library.gemm_op.GemmOperation"]:  # type: ignore[name-defined]  # noqa: F821
        """
        Filter ops without using information about the torch op, input nodes and output node.
        """
        assert cutlass_utils.try_import_cutlass()
        import cutlass_library.library as cutlass_lib  # type: ignore[import]

        # Skip simt kernels
        ops = [
            op
            for op in ops
            if op.tile_description.math_instruction.opcode_class
            != cutlass_lib.OpcodeClass.Simt
        ]

        # only keep the set of row x column ops
        # for other layout, we modify in place in filter_op, after deepcopy
        ops = [
            op
            for op in ops
            if op.A.layout.name == "RowMajor" and op.B.layout.name == "ColumnMajor"
        ]

        # filter by supported accumulator types
        ops = [
            op
            for op in ops
            if any(
                dtype_match(torch_dtype, op.accumulator_type())
                for torch_dtype in ACCUMULATOR_DTYPES
            )
        ]

        # check if dtypes of A and B are supported
        ops = [
            op
            for op in ops
            if any(dtype_match(torch_dtype, op.A.element) for torch_dtype in XW_DTYPES)
            and any(dtype_match(torch_dtype, op.B.element) for torch_dtype in XW_DTYPES)
        ]

        return ops