def seq_from_insts(self, insts):
        labels = {item for item in insts if isinstance(item, self.Label)}
        for i, lbl in enumerate(labels):
            lbl.value = i

        seq = _testinternalcapi.new_instruction_sequence()
        for item in insts:
            if isinstance(item, self.Label):
                seq.use_label(item.value)
            else:
                op = item[0]
                if isinstance(op, str):
                    op = opcode.opmap[op]
                arg, *loc = item[1:]
                if isinstance(arg, self.Label):
                    arg = arg.value
                loc = loc + [-1] * (4 - len(loc))
                seq.addop(op, arg or 0, *loc)
        return seq