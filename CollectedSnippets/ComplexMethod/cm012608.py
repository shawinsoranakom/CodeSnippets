def codegen_static_numels(self, code):
        """
        We get a small speedup from hard coding numels if they are static.

        This code stomps on the passed-in values by writing an constant to the top of the kernel.

        In a kernel like:
        def KERNEL_NAME(in_ptr0, in_ptr1, out_ptr2, xnumel, r0_numel, XBLOCK : tl.constexpr, R0_BLOCK : tl.constexpr):

        We would add
        xnumel = 4096
        r0_numel = 768

        After the signature, before the kernel code, if we decided to make these static. As its hardcoded, it becomes
        a better signal to triton on how to unroll and do some static indexing. So, it's not so much that downstream
        knows that its a static numel, as that you just plop a constant into the kernel.
        """

        def is_static_integer(expr: sympy.Expr) -> bool:
            return isinstance(expr, (sympy.Integer, int))

        for tree in self.range_trees:
            if not tree.is_reduction or self.inside_reduction:
                simplified_tree_numel = V.graph.sizevars.simplify(tree.numel)
                if is_static_integer(simplified_tree_numel):
                    code.writeline(f"{tree.prefix}numel = {int(simplified_tree_numel)}")

            if tree.is_reduction and self.persistent_reduction:
                if self.cooperative_reduction:
                    numel = self.kexpr(self.rename_indexing(tree.numel))
                    val = f"triton_helpers.constexpr_next_power_of_2(({numel} + RSPLIT - 1) // RSPLIT)"
                else:
                    val = self._get_persistent_RBLOCK(tree.numel)
                    if self.is_native_matmul:
                        # tl.dot only supports shapes >= 16
                        val = max(val, 16)

                code.writeline(f"{tree.prefix.upper()}BLOCK: tl.constexpr = {val}")

            if tree.prefix == "x" and self.no_x_dim:
                code.writeline("XBLOCK: tl.constexpr = 1")