def UNPACK_SEQUENCE(self, inst: Instruction) -> None:
        seq = self.pop()
        if seq.is_tensor():
            val = seq.unpack_var_sequence(self, idxes=range(inst.argval))  # type: ignore[arg-type]
        elif isinstance(seq, GetAttrVariable) and seq.obj.is_tensor():
            # x, y = a.shape
            proxy = getattr(seq.obj.as_proxy(), seq.name)
            val = [wrap_fx_proxy(self, proxy[i]) for i in range(inst.argval)]
        elif seq.has_force_unpack_var_sequence(self):
            val = seq.force_unpack_var_sequence(self)
        else:
            unimplemented(
                gb_type="Failed to unpack object for UNPACK_SEQUENCE",
                context=str(seq),
                explanation=f"{seq} cannot be unpacked into a list for the UNPACK_SEQUENCE bytecode "
                "(i.e. `a, b, c = d`).",
                hints=[*graph_break_hints.USER_ERROR],
            )
        if len(val) != inst.argval:
            unimplemented(
                gb_type="Length mismatch when unpacking object for UNPACK_SEQUENCE",
                context=f"expected length: {inst.argval}, actual: {len(val)}",
                explanation=f"{seq} unpacked to a list for the UNPACK_SEQUENCE bytecode "
                "(i.e. `a, b, c = d`) with unexpected length.",
                hints=[*graph_break_hints.DYNAMO_BUG],
            )
        for i in reversed(val):
            self.push(i)