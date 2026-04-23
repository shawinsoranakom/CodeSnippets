def codegen_static_numels_sub_kernel(
        self, code: IndentedBuffer, sub_kernel: TritonKernel, num: int
    ) -> list[str]:
        """
        We get a small speedup from hard coding numels if they are static.

        This code stomps on the passed-in values by writing an constant to the top of the kernel.

        In a kernel like:
        def KERNEL_NAME(in_ptr0, in_ptr1, out_ptr2, xnumel, rnumel, XBLOCK : tl.constexpr, R0_BLOCK : tl.constexpr):

        We would add
        xnumel = 4096
        rnumel = 768

        After the signature, before the kernel code, if we decided to make these static. As its hardcoded, it becomes
        a better signal to triton on how to unroll and do some static indexing. So, it's not so much that downstream
        knows that its a static numel, as that you just plop a constant into the kernel.
        """
        grid = []
        uniquify_block_sizes = []
        for tree in sub_kernel.range_trees:
            simplified_tree_numel = V.graph.sizevars.simplify(tree.numel)
            if isinstance(simplified_tree_numel, (Integer, int)):
                code.writeline(f"{tree.prefix}numel = {int(simplified_tree_numel)}")
            else:
                assert f"{tree.prefix}numel_{num}" in self.dynamic_shape_args
                uniquify_block_sizes.append(f"{tree.prefix}numel")

            if not tree.is_reduction:
                if isinstance(simplified_tree_numel, (Integer, int)):
                    grid.append(int(simplified_tree_numel))
                else:
                    # pyrefly: ignore [bad-argument-type]
                    grid.append(f"{tree.prefix}numel_{num}")

            if tree.is_reduction and sub_kernel.persistent_reduction:
                if isinstance(simplified_tree_numel, (Integer, int)):
                    val = int(simplified_tree_numel)
                else:
                    raise RuntimeError(
                        "Dynamic shape on reduction dimension is not supported"
                    )
                val = next_power_of_2(val)
                code.writeline(
                    f"{tree.prefix.upper()}BLOCK_{num}: tl.constexpr = {val}"
                )

            if tree.prefix == "x" and sub_kernel.no_x_dim:
                code.writeline(f"XBLOCK_{num}: tl.constexpr = 1")
                uniquify_block_sizes.append("XBLOCK")
            elif tree.prefix in ("x", "y") and config.combo_kernel_per_subkernel_blocks:
                uniquify_block_sizes.append(f"{tree.prefix.upper()}BLOCK")
            elif tree.is_reduction:
                if (
                    config.combo_kernel_per_subkernel_blocks
                    or sub_kernel.persistent_reduction
                ):
                    uniquify_block_sizes.append(f"{tree.prefix.upper()}BLOCK")
        self.grids.append(grid)
        return uniquify_block_sizes