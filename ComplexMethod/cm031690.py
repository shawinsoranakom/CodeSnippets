def _dump_stencil(opname: str, group: _stencils.StencilGroup) -> typing.Iterator[str]:
    yield "void"
    yield f"emit_{opname}("
    yield "    unsigned char *code, unsigned char *data, _PyExecutorObject *executor,"
    yield "    const _PyUOpInstruction *instruction, jit_state *state)"
    yield "{"
    for part, stencil in [("code", group.code), ("data", group.data)]:
        for line in stencil.disassembly:
            yield f"    // {line}"
        stripped = stencil.body.rstrip(b"\x00")
        if stripped:
            yield f"    const unsigned char {part}_body[{len(stencil.body)}] = {{"
            for i in range(0, len(stripped), 8):
                row = " ".join(f"{byte:#04x}," for byte in stripped[i : i + 8])
                yield f"        {row}"
            yield "    };"
    # Data is written first (so relaxations in the code work properly):
    for part, stencil in [("data", group.data), ("code", group.code)]:
        if stencil.body.rstrip(b"\x00"):
            yield f"    memcpy({part}, {part}_body, sizeof({part}_body));"
        stencil.holes.sort(key=lambda hole: hole.offset)
        for hole in stencil.holes:
            yield f"    {hole.as_c(part)}"
    yield "}"
    yield ""