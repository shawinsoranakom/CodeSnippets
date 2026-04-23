def setup_dom_indexing(self):
        """RDom based indexing uses explicit iteration ranges for Func updates"""
        prefix = "i" if self.inside_reduction else "o"
        if prefix in self.dom_renames:
            return self.dom_renames[prefix]

        renames = {}
        for var in self.halide_vars:
            if not self.inside_reduction and var in self.reduction_renames:
                continue
            m = re.match(r"^h(\d+)$", var.name)
            assert m
            renames[var] = sympy_index_symbol(f"h{prefix}{m.group(1)}")

        self.codegen_rdom(
            f"{prefix}dom", {rv: self.halide_vars[v] for v, rv in renames.items()}
        )

        self.dom_renames[prefix] = renames
        return renames