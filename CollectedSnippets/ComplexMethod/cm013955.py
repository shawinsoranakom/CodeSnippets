def _handle_comprehension_graph_break(
    tx: InstructionTranslatorBase, inst: Instruction
) -> None:
    """Handle list/dict comprehension graph break.

    Builds a synthetic function wrapping the comprehension bytecode,
    calls it via codegen_call_resume, then chains into the resume
    function for the post-comprehension code.
    """
    assert sys.version_info >= (3, 12)
    assert tx.instruction_pointer is not None

    start_ip = tx.instruction_pointer - 1  # BUILD_LIST/BUILD_MAP
    analysis = _analyze_comprehension(tx)
    stack_pops = 1 + len(analysis.iterator_vars)
    reason = GraphCompileReason("comprehension_graph_break", [tx.frame_summary()])
    log.debug("comprehension triggered compile")

    # --- Step 1: Compile the graph up to the comprehension ---

    all_stack_locals_metadata = tx.output.compile_subgraph(
        tx,
        reason=reason,
        stack_pops=stack_pops,
    )
    # Record which stack_pops items are NULL before popn loses the info.
    # NULLs on the CPython stack can't be passed as function arguments.
    stack_pops_null_mask = [
        isinstance(tx.stack[len(tx.stack) - stack_pops + i], NullVariable)
        for i in range(stack_pops)
    ]

    tx.popn(stack_pops)
    meta = all_stack_locals_metadata[0]
    cg = PyCodegen(tx.output.root_tx)

    # Runtime stack after compile_subgraph:
    #   cells, [frame_values], *(non-popped items), *(stack_pops items w/ NULLs)
    # frame_values[0] = [frame N locals] (no stack items yet)

    nonnull_count = sum(1 for m in stack_pops_null_mask if not m)

    # live_stack_depth: stack items above cells/frame_values excluding NULLs
    # that compile_subgraph didn't codegen (tracked in stack_null_idxes).
    live_stack_depth = len(tx.stack) - len(meta.stack_null_idxes)

    # --- Step 2: Pop stack_pops items and append non-nulls to frame_values[0] ---
    # SWAP each item to TOS then LIST_APPEND or pop_null; fv_list stays at
    # TOS throughout. Items append in TOS-first (reversed) order;
    # _build_comprehension_fn compensates by loading in reverse.
    cg.extend_output(
        [
            # frame_values[0] to TOS
            *create_copy(live_stack_depth + stack_pops + 1),
            cg.create_load_const(0),
            cg.create_binary_subscr(),
        ]
    )
    for i in reversed(range(stack_pops)):
        cg.extend_output(create_swap(2))
        if stack_pops_null_mask[i]:
            cg.extend_output(cg.pop_null())
        else:
            cg.extend_output([create_instruction("LIST_APPEND", arg=1)])
    cg.extend_output([create_instruction("POP_TOP")])

    # Stack: cells, [frame_values], *(non-popped items)

    # --- Step 3: Build comprehension function ---
    new_code, fn_name = _build_comprehension_fn(
        tx,
        analysis,
        start_ip,
        stack_pops,
        stack_pops_null_mask,
        nonnull_count,
        meta,
    )

    # --- Step 4: Extract [cells[0]] and [frame_values[0]] for codegen_call_resume ---
    cg.extend_output(
        [
            *create_copy(live_stack_depth + 2),
            cg.create_load_const(0),
            cg.create_binary_subscr(),
            create_instruction("BUILD_LIST", arg=1),
            *create_copy(live_stack_depth + 2),
            cg.create_load_const(0),
            cg.create_binary_subscr(),
            create_instruction("BUILD_LIST", arg=1),
        ]
    )

    # Stack: ..., *(non-popped), [cells[0]], [frame_values[0]]

    # --- Step 5: Call comprehension function via codegen_call_resume ---
    tx.codegen_call_resume([new_code], [fn_name], cg)

    # Stack: ..., *(non-popped), comp_result

    # --- Step 6: Remove appended stack_pops items from frame_values[0] ---
    if nonnull_count > 0:
        frame_values_pos = live_stack_depth + 1 + 1  # +1 result, +1 frame_values
        cg.extend_output(
            [
                *create_copy(frame_values_pos),
                cg.create_load_const(0),
                cg.create_binary_subscr(),
                # frame_values[0] on TOS
                create_dup_top(),
                # frame_values[0], frame_values[0]
                cg.create_load_const(-nonnull_count),
                cg.create_load_const(None),
                create_instruction("BUILD_SLICE", arg=2),
                create_instruction("DELETE_SUBSCR"),
                # del frame_values[0][-nonnull_count:]
                create_instruction("POP_TOP"),
            ]
        )

    # --- Step 7: Pass comprehension outputs to frame_values[0] ---
    # Walrus vars first, then result_var.
    vars_to_pass = analysis.walrus_vars + (
        [analysis.result_var] if analysis.result_var else []
    )

    existing_vars: dict[str, int] = {}
    for var_name in vars_to_pass:
        tx.symbolic_locals[var_name] = UnknownVariable()
        if var_name in meta.locals_names:
            existing_vars[var_name] = meta.locals_names[var_name]
        else:
            meta.locals_names[var_name] = len(meta.locals_names)

    fv_depth = live_stack_depth + 2  # comp_result + frame_values

    # --- Walrus vars: extract from comp_result tuple ---
    if analysis.walrus_vars:
        # comp_result is (result, *walrus_vars).
        cg.extend_output(
            [
                *create_copy(fv_depth),
                cg.create_load_const(0),
                cg.create_binary_subscr(),
            ]
        )
        # Stack: ..., comp_tuple, fv0
        for j, walrus_var in enumerate(analysis.walrus_vars):
            cg.extend_output(
                [
                    *create_copy(2),
                    cg.create_load_const(j + 1),
                    cg.create_binary_subscr(),
                ]
            )
            # Stack: ..., comp_tuple, fv0, walrus_value
            if walrus_var in existing_vars:
                # fv0[idx] = walrus_value
                cg.extend_output(
                    [
                        *create_copy(2),  # copy fv0
                        cg.create_load_const(existing_vars[walrus_var]),
                        create_instruction("STORE_SUBSCR"),
                    ]
                )
            else:
                cg.extend_output([create_instruction("LIST_APPEND", arg=1)])
            # Stack: ..., comp_tuple, fv0
        cg.extend_output(
            [
                create_instruction("POP_TOP"),  # pop fv0
                # Extract the result from the tuple.
                cg.create_load_const(0),
                cg.create_binary_subscr(),
            ]
        )
        # Stack: ..., result

    # --- Result: keep on stack, overwrite/append to fv[0], or discard ---
    if analysis.result_on_stack:
        tx.push(UnknownVariable())
    elif analysis.result_var:
        cg.extend_output(
            [
                *create_copy(fv_depth),
                cg.create_load_const(0),
                cg.create_binary_subscr(),
                # Stack: ..., result, fv0
            ]
        )
        if analysis.result_var in existing_vars:
            cg.extend_output(
                [
                    cg.create_load_const(existing_vars[analysis.result_var]),
                    create_instruction("STORE_SUBSCR"),
                    # fv0[idx] = result
                ]
            )
        else:
            cg.extend_output(
                [
                    *create_swap(2),
                    create_instruction("LIST_APPEND", arg=1),
                    create_instruction("POP_TOP"),
                ]
            )
    else:
        cg.extend_output([create_instruction("POP_TOP")])

    # Stack: cells, [frame_values], *(non-popped stack)
    tx.output.add_output_instructions(cg.get_instructions())

    # --- Step 8: Create resume function chain ---
    resume_inst = tx.instructions[analysis.end_ip]
    tx.output.add_output_instructions(
        tx.create_call_resume_at(resume_inst, all_stack_locals_metadata)
    )

    tx.instruction_pointer = None