def inline_asm_elementwise(
        *inputs,
        asm,
        constraints=None,
        dtype=torch.float32,
        is_pure=True,
        pack=1,
        input_dtypes=None,
    ):
        # Use the actual dtype, not the compute type — the asm operates on
        # specific register types and Triton needs to know the real output type.
        asm_triton_type = triton_type(dtype)
        if constraints is None:
            constraints = ", ".join(["=r"] + ["r" for _ in inputs])

        # Inductor computes bf16/fp16 in fp32. For "h" (16-bit register)
        # constraints, cast back to the original dtype so the asm sees the
        # right register type.
        constraint_parts = [p.strip() for p in constraints.split(",")]
        input_constraints = [p for p in constraint_parts if not p.startswith("=")]
        cast_inputs = []
        for i, (inp, c) in enumerate(zip(inputs, input_constraints[: len(inputs)])):
            if (
                c == "h"
                and input_dtypes is not None
                and isinstance(inp, CSEVariable)
                and inp.dtype != input_dtypes[i]
            ):
                cast_inputs.append(f"{inp}.to({triton_type(input_dtypes[i])})")
            else:
                cast_inputs.append(str(inp))

        if torch.version.hip:
            # AMDGCN asm strings may contain real newlines (instructions are
            # newline-separated, unlike PTX which uses semicolons).  The
            # generated code is nested inside two Python string layers:
            #   Layer 1 : the cached wrapper .py file
            #   Layer 2 : the Triton kernel source (a triple-quoted string
            #             inside that wrapper, exec'd / JIT-compiled)
            # repr() escapes \n -> \\n, then we double the backslashes so
            # they survive both layers: \\\\n -> (L1 parse) \\n -> (L2 parse) \n.
            asm_literal = repr(asm).replace("\\", "\\\\")
            constraints_literal = repr(constraints).replace("\\", "\\\\")
        else:
            asm_literal = f"'{asm}'"
            constraints_literal = f"'{constraints}'"

        def asm_call(args):
            return (
                f"tl.inline_asm_elementwise({asm_literal}, {constraints_literal}, "
                f"[{args}], dtype={asm_triton_type}, is_pure={is_pure}, pack={pack})"
            )

        if pack <= 1:
            return asm_call(", ".join(cast_inputs))

        first_input = inputs[0]
        compute = V.kernel.compute
        cse = V.kernel.cse
        result = cse.newvar(dtype=dtype, shape=first_input.shape)
        packed_args = ", ".join(
            f"triton_helpers.inline_asm_pack({inp}, {pack})" for inp in cast_inputs
        )
        compute.writeline(f"{result} = {asm_call(packed_args)}")
        compute.writeline(
            f"{result} = triton_helpers.inline_asm_unpack({result}, {first_input}, {pack})"
        )
        return result