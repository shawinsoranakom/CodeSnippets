def analyze_forest(forest: list[parser.AstNode]) -> Analysis:
    instructions: dict[str, Instruction] = {}
    uops: dict[str, Uop] = {}
    families: dict[str, Family] = {}
    pseudos: dict[str, PseudoInstruction] = {}
    labels: dict[str, Label] = {}
    for node in forest:
        match node:
            case parser.InstDef(name):
                if node.kind == "inst":
                    desugar_inst(node, instructions, uops)
                else:
                    assert node.kind == "op"
                    add_op(node, uops)
            case parser.Macro():
                pass
            case parser.Family():
                pass
            case parser.Pseudo():
                pass
            case parser.LabelDef():
                pass
            case _:
                assert False
    for node in forest:
        if isinstance(node, parser.Macro):
            add_macro(node, instructions, uops)
    for node in forest:
        match node:
            case parser.Family():
                add_family(node, instructions, families)
            case parser.Pseudo():
                add_pseudo(node, instructions, pseudos)
            case parser.LabelDef():
                add_label(node, labels)
            case _:
                pass
    for uop in uops.values():
        uop.instruction_size = get_instruction_size_for_uop(instructions, uop)
    # Special case BINARY_OP_INPLACE_ADD_UNICODE
    # BINARY_OP_INPLACE_ADD_UNICODE is not a normal family member,
    # as it is the wrong size, but we need it to maintain an
    # historical optimization.
    if "BINARY_OP_INPLACE_ADD_UNICODE" in instructions:
        inst = instructions["BINARY_OP_INPLACE_ADD_UNICODE"]
        inst.family = families["BINARY_OP"]
        families["BINARY_OP"].members.append(inst)
    opmap, first_arg, min_instrumented = assign_opcodes(instructions, families, pseudos)
    return Analysis(
        instructions, uops, families, pseudos, labels, opmap, first_arg, min_instrumented
    )