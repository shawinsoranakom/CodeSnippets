def get_block_args(self) -> list[ConstexprArg]:
        """
        Calculate blocks from sub_kernels and range_trees.
        Update self.block_args, self.y_tree_list
        Return the block args
        """
        block_names = {}
        for i, sub_kernel in enumerate(self.sub_kernels):
            y_tree = None
            for tree in sub_kernel.range_trees:
                if tree.is_reduction and (
                    not sub_kernel.inside_reduction or sub_kernel.persistent_reduction
                ):
                    continue
                if tree.prefix == "x" and sub_kernel.no_x_dim:
                    continue
                if tree.prefix == "y":
                    y_tree = tree
                if config.combo_kernel_per_subkernel_blocks:
                    block_names[f"{tree.prefix.upper()}BLOCK_{i}"] = tree.prefix
                else:
                    block_names[f"{tree.prefix.upper()}BLOCK"] = tree.prefix
            self.y_tree_list.append(y_tree)
        self.block_args = list(block_names.keys())

        return [ConstexprArg(x) for x in block_names]