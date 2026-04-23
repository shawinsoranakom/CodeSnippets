def _analyze_comprehension(tx: InstructionTranslatorBase) -> ComprehensionAnalysis:
    """Analyze comprehension bytecode to determine result handling pattern."""
    assert sys.version_info >= (3, 12)
    assert tx.instruction_pointer is not None

    patterns = _get_comprehension_result_patterns()
    start_ip = tx.instruction_pointer - 1  # BUILD_LIST/BUILD_MAP

    iterator_vars: list[str] = []
    walrus_vars: list[str] = []
    captured_vars: list[str] = []
    defined_inside: set[str] = set()

    # Collect iterator variables from LOAD_FAST_AND_CLEAR before BUILD_LIST/BUILD_MAP
    iter_scan_ip = start_ip - 1
    while iter_scan_ip >= 0:
        inst = tx.instructions[iter_scan_ip]
        if inst.opname == "LOAD_FAST_AND_CLEAR":
            iterator_vars.insert(0, inst.argval)
            iter_scan_ip -= 1
        elif inst.opname in ("SWAP", "GET_ITER"):
            iter_scan_ip -= 1
        else:
            break
    defined_inside.update(iterator_vars)

    end_for_ip = _find_comprehension_end_for_ip(tx)
    if end_for_ip == -1:
        unimplemented(
            gb_type="Comprehension analysis failed: No END_FOR",
            context="",
            explanation="Could not find END_FOR instruction in comprehension bytecode.",
            hints=[],
        )

    # Find first FOR_ITER to know where loop body starts
    for_iter_ip = next(
        i
        for i in range(start_ip, end_for_ip)
        if tx.instructions[i].opname == "FOR_ITER"
    )

    # Single pass through loop body to detect walrus vars and captured vars
    for body_ip in range(for_iter_ip + 1, end_for_ip):
        inst = tx.instructions[body_ip]

        # Detect walrus pattern: COPY 1 followed by STORE_FAST
        if inst.opname == "COPY" and inst.arg == 1 and body_ip + 1 < end_for_ip:
            next_inst = tx.instructions[body_ip + 1]
            if next_inst.opname == "STORE_FAST":
                var_name = next_inst.argval
                if var_name not in iterator_vars and var_name not in walrus_vars:
                    walrus_vars.append(var_name)
                    defined_inside.add(var_name)

        # Track variables defined inside the loop
        if inst.opname == "STORE_FAST":
            defined_inside.add(inst.argval)

        # Detect LOAD_FAST referencing outer variables
        elif inst.opname.startswith("LOAD_FAST"):
            var_names = (
                inst.argval if isinstance(inst.argval, tuple) else (inst.argval,)
            )
            for var_name in var_names:
                if var_name not in defined_inside and var_name not in captured_vars:
                    captured_vars.append(var_name)

    # Extract pre_store_ops: all opcodes from END_FOR+1 until first STORE_FAST
    pre_store_ops: list[str] = []
    scan_ip = end_for_ip + 1
    while (
        scan_ip < len(tx.instructions)
        and tx.instructions[scan_ip].opname != "STORE_FAST"
    ):
        pre_store_ops.append(tx.instructions[scan_ip].opname)
        scan_ip += 1

    store_fast_ip = scan_ip

    # Skip all STORE_FASTs to find post_store_op
    while (
        scan_ip < len(tx.instructions)
        and tx.instructions[scan_ip].opname == "STORE_FAST"
    ):
        scan_ip += 1

    post_store_op = (
        tx.instructions[scan_ip].opname if scan_ip < len(tx.instructions) else None
    )

    def matches(name: str) -> bool:
        pat = patterns[name]
        return pre_store_ops == pat["pre_store_ops"] and (
            post_store_op == pat["post_store_op"] or not pat["post_store_op"]
        )

    result_var: str | None = None
    if matches("stored"):
        result_var = tx.instructions[store_fast_ip].argval
        result_on_stack = False
    elif matches("discarded"):
        result_var = None
        result_on_stack = False
        scan_ip = scan_ip + 1 if patterns["discarded"]["post_store_op"] else scan_ip
    elif matches("returned") or pre_store_ops == patterns["consumed"]["pre_store_ops"]:
        result_var = None
        result_on_stack = True
    else:
        unimplemented(
            gb_type="Comprehension analysis failed: No matches",
            context=f"pre_store_ops={pre_store_ops}, post_store_op={post_store_op}",
            explanation="Comprehension does not match any known bytecode pattern.",
            hints=[],
        )

    return ComprehensionAnalysis(
        end_ip=scan_ip,
        result_var=result_var,
        # pyrefly: ignore [unbound-name]
        result_on_stack=result_on_stack,
        iterator_vars=iterator_vars,
        walrus_vars=walrus_vars,
        captured_vars=captured_vars,
    )