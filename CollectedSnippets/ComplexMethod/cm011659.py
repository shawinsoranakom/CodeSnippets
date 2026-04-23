def use_cpp_bmm_template(
    layout: Layout, mat1: ReinterpretView | Buffer, mat2: IRNode
) -> bool:
    from .ir import Layout

    assert isinstance(mat1.layout, Layout)

    # In certain scenarios, such as when the first stride is 0, the entire tensor may not be contiguous.
    # But the 2D matrix within each batch can still be contiguous, allowing us to apply max autotune.
    # So here we specifically check for contiguity within the 2D matrix of each batch.
    mat1_size = mat1.layout.size
    mat1_stride = mat1.layout.stride
    mat1_each_batch_is_contiguous = (
        _use_template_for_cpu(layout)
        and mat1.get_dtype() == torch.float32
        and (len(mat1_size) == 3)
        and (len(mat1_stride) == 3)
        and (mat1_stride[1] == mat1_size[2])
        and (mat1_stride[2] == 1)
    )
    return use_cpp_gemm_template(layout, mat1, mat2, require_constant_mat2=False) and (
        mat1.layout.is_contiguous() or mat1_each_batch_is_contiguous
    )