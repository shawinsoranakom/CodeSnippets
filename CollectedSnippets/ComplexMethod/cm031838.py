def for_uop(stack: Stack, uop: Uop, out: CWriter, check_liveness: bool = True) -> "Storage":
        inputs: list[Local] = []
        peeks: list[Local] = []
        for input in reversed(uop.stack.inputs):
            local = stack.pop(input, out)
            if input.peek:
                peeks.append(local)
            inputs.append(local)
        inputs.reverse()
        peeks.reverse()
        offset = stack.logical_sp - stack.physical_sp
        for ouput in uop.stack.outputs:
            if ouput.is_array() and ouput.used and not ouput.peek:
                c_offset = offset.to_c()
                out.emit(f"{ouput.name} = &stack_pointer[{c_offset}];\n")
            offset = offset.push(ouput)
        for var in inputs:
            stack.push(var)
        outputs = peeks + [ Local.undefined(var) for var in uop.stack.outputs if not var.peek ]
        return Storage(stack, inputs, outputs, len(peeks), check_liveness)