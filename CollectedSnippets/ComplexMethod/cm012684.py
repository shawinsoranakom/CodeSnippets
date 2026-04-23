def _calculate_total_blocks(
            cls, kernel: "ComboKernel", code: IndentedBuffer
        ) -> None:
            """
            Calculate total blocks for each subkernel (x_blocks * y_blocks)
            and cumulative block counts for dispatch boundaries.
            """
            for i, sub_kernel in enumerate(kernel.sub_kernels):
                no_x_dim = sub_kernel.no_x_dim
                xnumel = (
                    kernel.min_x_blocks_list[i] if no_x_dim else kernel.x_numels_list[i]
                )
                x_blocks_str = (
                    f"tl.cdiv({xnumel}, XBLOCK_{i})" if not no_x_dim else f"{xnumel}"
                )
                code.splice(f"x_blocks_{i} = {x_blocks_str}")

                if kernel.y_tree_list[i]:
                    numel = V.graph.sizevars.simplify(kernel.y_tree_list[i].numel)
                    ynumel = (
                        int(numel)
                        if isinstance(numel, (Integer, int))
                        else f"ynumel_{i}"
                    )
                    code.splice(f"y_blocks_{i} = tl.cdiv({ynumel}, YBLOCK_{i})")

                blocks_expr = (
                    f"x_blocks_{i} * y_blocks_{i}"
                    if kernel.y_tree_list[i]
                    else f"x_blocks_{i}"
                )
                code.splice(
                    f"num_blocks_{i} = {blocks_expr}"
                    if i == 0
                    else f"num_blocks_{i} = num_blocks_{i - 1} + {blocks_expr}"
                )