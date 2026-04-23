def _calculate_xblocks(
            cls, kernel: "ComboKernel", code: IndentedBuffer
        ) -> None:
            x_numels_list = kernel.x_numels_list
            for i in range(len(x_numels_list)):
                xnumels, no_x_dim = (
                    (x_numels_list[i], False)
                    if isinstance(x_numels_list[i], str)
                    and cast(str, x_numels_list[i])[0] != "-"
                    or (
                        isinstance(x_numels_list[i], int)
                        and cast(int, x_numels_list[i]) > 0
                    )
                    else (kernel.min_x_blocks_list[i], True)
                )
                xblock_str = (
                    f"tl.cdiv({xnumels}, XBLOCK)" if not no_x_dim else f"{xnumels}"
                )
                if i == 0:
                    code.splice(f"num_xblocks_{i} = {xblock_str}")
                else:
                    code.splice(f"num_xblocks_{i} = num_xblocks_{i - 1} + {xblock_str}")