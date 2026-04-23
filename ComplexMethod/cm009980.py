def name(self) -> str | None:
        """
        Extract variable name from current instruction.
        """
        opname = self.opcode()
        if not opname:
            return None

        names = None
        if opname in ("STORE_NAME", "STORE_GLOBAL"):
            names = self.code_object.co_names
        elif opname == "STORE_FAST":
            names = self.code_object.co_varnames
        elif opname == "STORE_DEREF":
            names = self.code_object.co_cellvars
            if not names:
                names = self.code_object.co_freevars
        else:
            return None

        arg = self.oparg()
        if names and 0 <= arg < len(names):
            return names[arg]

        return None