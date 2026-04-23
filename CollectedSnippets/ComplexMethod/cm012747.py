def _define_gemm_instance(
        self,
        op: GemmOperation,
        evt_name: str | None = None,
    ) -> tuple[str, str]:
        """Defines and renders the Cutlass / CUDA/XPU C++ code for a given GEMM operation instance.

        This function uses the Cutlass library to generate key parts of the codegen process. General Matrix Multiply
        forms a core part of a number of scientific applications, so this efficient and adaptable implementation is
        crucial.

        Args:
            op (cutlass_library.gemm_op.GemmOperation): This is the core GEMM operation that we are defining and rendering.

        Returns:
            tuple[str, str]: A tuple where the first part is a string that constitutes the defined GEMM operation in C++
                             code (render) and the second part is the string that specifies the operation type.
        """
        assert cutlass_utils.try_import_cutlass()
        import cutlass_library.library as cutlass_lib

        from .lib_extensions import gemm_operation_extensions as gemm_extensions

        emitter = gemm_extensions.EmitGemmUniversal3xInstanceWithEVT(
            evt_name=evt_name, device_type=self.device_type
        )  # type: ignore[call-arg]

        if not hasattr(op, "epilogue_functor") or not isinstance(
            op.epilogue_functor, enum.Enum
        ):
            op = copy.deepcopy(op)
            op.epilogue_functor = cutlass_lib.EpilogueFunctor.LinearCombination

        op_def = emitter.emit(op)
        pattern = re.compile(r"\s*struct\s(.*?)\s:")
        decl = [line for line in op_def.split("\n") if "struct " in line][-1]

        match = pattern.match(decl)
        if match is None:
            raise RuntimeError("Invalid Gemm config: \n" + op_def)
        op_type = match.groups()[0]
        if op.gemm_kind == cutlass_lib.GemmKind.Universal3x:
            op_def += f"\n  using {op_type}_device_type = cutlass::gemm::device::GemmUniversalAdapter<{op_type}>;\n"
            op_type = f"{op_type}_device_type"

        return op_def, op_type