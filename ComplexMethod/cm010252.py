def _bsr_strided_addmm_kernel(
        # values prologue
        values_ptr,
        values_batch_stride,
        values_nnz_stride,
        values_row_block_stride,
        values_col_block_stride,
        # values epilogue
        # crow_indices prologue
        crow_indices_ptr,
        crow_indices_batch_stride,
        crow_indices_stride,
        # crow_indices epilogue
        # col_indices prologue
        col_indices_ptr,
        col_indices_batch_stride,
        col_indices_stride,
        # col_indices epilogue
        # input prologue
        input_ptr,
        input_batch_stride,
        input_tiled_row_stride,
        input_tiled_col_stride,
        input_row_block_stride,
        input_col_block_stride,
        # input epilogue
        # dense prologue
        dense_ptr,
        dense_batch_stride,
        dense_tiled_row_stride,
        dense_tiled_col_stride,
        dense_row_block_stride,
        dense_col_block_stride,
        # dense epilogue
        # left_alpha prologue
        left_alpha_ptr,
        left_alpha_batch_stride,
        left_alpha_tiled_row_stride,
        left_alpha_tiled_col_stride: tl.constexpr,
        left_alpha_row_block_stride,
        left_alpha_col_block_stride: tl.constexpr,
        # left_alpha epilogue
        # right_alpha prologue
        right_alpha_ptr,
        right_alpha_batch_stride,
        right_alpha_tiled_row_stride: tl.constexpr,
        right_alpha_tiled_col_stride,
        right_alpha_row_block_stride: tl.constexpr,
        right_alpha_col_block_stride,
        # right_alpha epilogue
        # output prologue
        output_ptr,
        output_batch_stride,
        output_tiled_row_stride,
        output_tiled_col_stride,
        output_row_block_stride,
        output_col_block_stride,
        # output epilogue
        beta,
        alpha,
        beta_is_one: tl.constexpr,
        beta_is_nonzero: tl.constexpr,
        alpha_is_one: tl.constexpr,
        left_alpha_is_one: tl.constexpr,
        right_alpha_is_one: tl.constexpr,
        BLOCKSIZE_ROW: tl.constexpr,
        BLOCKSIZE_COL: tl.constexpr,
        BLOCKSIZE_INNER: tl.constexpr,
        acc_dtype: tl.constexpr,
        allow_tf32: tl.constexpr,
        GROUP_SIZE_ROW: tl.constexpr,
        SPLIT_N: tl.constexpr,
    ):
        # left/right_alpha tensors are originally (* + 1)-dimensional
        if left_alpha_tiled_col_stride != 0:
            raise AssertionError(
                f"left_alpha_tiled_col_stride must be 0, got {left_alpha_tiled_col_stride}"
            )
        if left_alpha_col_block_stride != 0:
            raise AssertionError(
                f"left_alpha_col_block_stride must be 0, got {left_alpha_col_block_stride}"
            )
        if right_alpha_tiled_row_stride != 0:
            raise AssertionError(
                f"right_alpha_tiled_row_stride must be 0, got {right_alpha_tiled_row_stride}"
            )
        if right_alpha_row_block_stride != 0:
            raise AssertionError(
                f"right_alpha_row_block_stride must be 0, got {right_alpha_row_block_stride}"
            )

        batch_pid = tl.program_id(axis=2)
        row_block_pid = tl.program_id(axis=0)
        col_block_pid = tl.program_id(axis=1)
        n_block_rows = tl.num_programs(axis=0)
        n_block_cols = tl.num_programs(axis=1)

        row_block_pid, col_block_pid = tl.swizzle2d(
            row_block_pid, col_block_pid, n_block_rows, n_block_cols, GROUP_SIZE_ROW
        )

        crow_indices_offset_ptr = (
            crow_indices_ptr
            + crow_indices_batch_stride * batch_pid
            + crow_indices_stride * row_block_pid
        )
        nnz_offset = tl.load(crow_indices_offset_ptr)
        nnz_offset_next = tl.load(crow_indices_offset_ptr + crow_indices_stride)

        # Compute nnz for the row with number row_block_pid.
        row_nnz = nnz_offset_next - nnz_offset

        row_block_arange = tl.arange(0, BLOCKSIZE_ROW)
        inner_block_arange = tl.arange(0, BLOCKSIZE_INNER)
        col_block_arange = tl.arange(0, BLOCKSIZE_COL)

        # Pointers are set to the first block of the current row.
        values_block_ptrs = (
            values_ptr
            + values_batch_stride * batch_pid
            + values_nnz_stride * nnz_offset
            + values_row_block_stride * row_block_arange[:, None]
            + values_col_block_stride * inner_block_arange[None, :]
        )

        # NOTE: dense is advanced into all dimensions but the tiled row one.
        # That will be advanced in the loop according to values in col_indices.
        dense_block_ptrs = (
            dense_ptr
            + dense_batch_stride * batch_pid
            + dense_tiled_col_stride * col_block_pid
            + dense_row_block_stride * inner_block_arange[:, None]
            + dense_col_block_stride * col_block_arange[None, :]
        )

        # Pointers are set to exact write-to locations
        output_ptrs = (
            output_ptr
            + output_batch_stride * batch_pid
            + output_tiled_row_stride * row_block_pid
            + output_tiled_col_stride * col_block_pid
            + output_row_block_stride * row_block_arange[:, None]
            + output_col_block_stride * col_block_arange[None, :]
        )

        # Set pointer to the first nonzero element in the current row
        col_index_nnz_ptr = (
            col_indices_ptr
            + col_indices_batch_stride * batch_pid
            + col_indices_stride * nnz_offset
        )

        output_acc_block = tl.zeros((BLOCKSIZE_ROW, BLOCKSIZE_COL), dtype=acc_dtype)

        for _ in range(row_nnz):
            values_block = tl.load(values_block_ptrs)

            # find which row of dense needs to get loaded
            # for multiplication with values_block.
            dense_row_idx = tl.load(col_index_nnz_ptr)
            dense_block = tl.load(
                dense_block_ptrs + dense_tiled_row_stride * dense_row_idx
            )

            # do block mm
            output_acc_block += tl.dot(
                values_block, dense_block, allow_tf32=allow_tf32, out_dtype=acc_dtype
            )

            # move val/col_index ptrs to the next block in the row
            values_block_ptrs += values_nnz_stride
            col_index_nnz_ptr += col_indices_stride

        if not alpha_is_one:
            output_acc_block *= alpha

        if not left_alpha_is_one:
            left_alpha_ptrs = (
                left_alpha_ptr
                + left_alpha_batch_stride * batch_pid
                + left_alpha_tiled_row_stride * row_block_pid
                + left_alpha_tiled_col_stride * col_block_pid
                + left_alpha_row_block_stride * row_block_arange[:, None]
                + left_alpha_col_block_stride * col_block_arange[None, :]
            )
            output_acc_block *= tl.load(left_alpha_ptrs)

        if not right_alpha_is_one:
            right_alpha_ptrs = (
                right_alpha_ptr
                + right_alpha_batch_stride * batch_pid
                + right_alpha_tiled_row_stride * row_block_pid
                + right_alpha_tiled_col_stride * col_block_pid
                + right_alpha_row_block_stride * row_block_arange[:, None]
                + right_alpha_col_block_stride * col_block_arange[None, :]
            )
            output_acc_block *= tl.load(right_alpha_ptrs)

        if beta_is_nonzero:
            input_ptrs = (
                input_ptr
                + input_batch_stride * batch_pid
                + input_tiled_row_stride * row_block_pid
                + input_tiled_col_stride * col_block_pid
                + input_row_block_stride * row_block_arange[:, None]
                + input_col_block_stride * col_block_arange[None, :]
            )
            if beta_is_one:
                output_acc_block += tl.load(input_ptrs)
            else:
                output_acc_block += beta * tl.load(input_ptrs)

        # write back the result
        tl.store(output_ptrs, output_acc_block.to(output_ptr.dtype.element_ty))