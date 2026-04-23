def add_macro(
    macro: parser.Macro, instructions: dict[str, Instruction], uops: dict[str, Uop]
) -> None:
    parts: list[Part] = []
    seen_real_uop = False
    for part in macro.uops:
        match part:
            case parser.OpName():
                if part.name == "flush":
                    parts.append(Flush())
                else:
                    if part.name not in uops:
                        raise analysis_error(
                            f"No Uop named {part.name}", macro.tokens[0]
                        )
                    uop = uops[part.name]
                    if uop.properties.records_value:
                        if seen_real_uop:
                            raise analysis_error(
                                f"Recording uop {part.name} must precede all "
                                f"non-recording, non-specializing uops in macro",
                                macro.tokens[0])
                    elif "specializing" not in uop.annotations:
                        seen_real_uop = True
                    parts.append(uop)
            case parser.CacheEffect():
                parts.append(Skip(part.size))
            case _:
                assert False
    assert parts
    add_instruction(macro.first_token, macro.name, parts, instructions)