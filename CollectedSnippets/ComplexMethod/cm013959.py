def update(instructions: list[Instruction], code_options: dict[str, Any]) -> None:
        code_options["co_name"] = fn_name
        if sys.version_info >= (3, 11):
            code_options["co_qualname"] = fn_name
        code_options["co_firstlineno"] = lineno
        code_options["co_cellvars"] = ()
        code_options["co_freevars"] = freevars
        code_options["co_argcount"] = len(args)
        code_options["co_posonlyargcount"] = 0
        code_options["co_kwonlyargcount"] = 0
        code_options["co_varnames"] = tuple(
            args + [v for v in comprehension_body_vars if v not in args]
        )
        code_options["co_flags"] = code_options["co_flags"] & ~(
            CO_VARARGS | CO_VARKEYWORDS
        )

        prefix: list[Instruction] = []
        if freevars:
            prefix.append(create_instruction("COPY_FREE_VARS", arg=len(freevars)))
        prefix.append(create_instruction("RESUME", arg=0))

        # Push stack_pops items onto operand stack so the comprehension
        # bytecode finds them where it expects (iterator + saved vars).
        # NULL positions get PUSH_NULL, non-null get LOAD_FAST.
        # Items were appended to frame_values[0] in TOS-first order,
        # so load in reverse to reconstruct the original stack layout.
        nonnull_i = nonnull_count - 1
        for i in range(stack_pops):
            if stack_pops_null_mask[i]:
                prefix.append(create_instruction("PUSH_NULL"))
            else:
                prefix.append(
                    create_instruction("LOAD_FAST", argval=f"___stack{nonnull_i}")
                )
                nonnull_i -= 1

        comp_insts = _copy_comprehension_bytecode(tx, start_ip, analysis.end_ip)

        # Epilogue: ensure result is on stack, pack walrus vars, return.
        epilogue: list[Instruction] = []
        if not analysis.result_on_stack:
            if analysis.result_var:
                epilogue.append(
                    create_instruction("LOAD_FAST", argval=analysis.result_var)
                )
            else:
                epilogue.append(create_instruction("LOAD_CONST", argval=None))
        if analysis.walrus_vars:
            for var_name in analysis.walrus_vars:
                epilogue.append(create_instruction("LOAD_FAST", argval=var_name))
            epilogue.append(
                create_instruction(
                    "BUILD_TUPLE",
                    arg=1 + len(analysis.walrus_vars),
                )
            )
        epilogue.append(create_instruction("RETURN_VALUE"))

        instructions[:] = prefix + comp_insts + epilogue