def kind_to_text(kind: int, opcode: str):
            if kind <= 8:
                return pretty(self._defines[kind][0])
            if opcode == "LOAD_SUPER_ATTR":
                opcode = "SUPER"
            elif opcode.endswith("ATTR"):
                opcode = "ATTR"
            elif opcode in ("FOR_ITER", "GET_ITER", "SEND"):
                opcode = "ITER"
            elif opcode.endswith("SUBSCR"):
                opcode = "SUBSCR"
            for name in self._defines[kind]:
                if name.startswith(opcode):
                    return pretty(name[len(opcode) + 1 :])
            return "kind " + str(kind)