def _code_to_bytes(self, code, context: Context, func=None) -> bytes:
        h = hashlib.new("md5")

        # Hash the bytecode.
        self.update(h, code.co_code)

        # Hash constants that are referenced by the bytecode but ignore names of lambdas.
        consts = [
            n
            for n in code.co_consts
            if not isinstance(n, str) or not n.endswith(".<lambda>")
        ]
        self.update(h, consts, context)

        context.cells.push(code, func=func)
        for ref in get_referenced_objects(code, context):
            self.update(h, ref, context)
        context.cells.pop()

        return h.digest()