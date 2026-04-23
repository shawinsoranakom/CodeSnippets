def use_cpp_gemm_template(
    layout: Layout,
    mat1: IRNode,
    mat2: IRNode,
    mat2_transposed: bool = False,
    require_constant_mat2: bool = True,
    is_woq_int4: bool = False,
    q_group_size: int | None = None,
) -> bool:
    from . import ir
    from .codegen.cpp_micro_gemm import create_micro_gemm
    from .codegen.cpp_utils import get_gemm_template_output_and_compute_dtype
    from .kernel.mm_common import mm_args

    if not _use_template_for_cpu(layout) or not _use_autotune_backend("CPP"):
        return False

    if not config.cpp.weight_prepack:
        return False

    int8_gemm = mat1.get_dtype() in [torch.uint8, torch.int8]
    layout_dtypes = [torch.float32, torch.bfloat16, torch.half, torch.uint8, torch.int8]
    m, n, k, layout, mat1, mat2 = mm_args(
        mat1,
        mat2,
        out_dtype=layout.dtype if int8_gemm else None,
        mat2_transposed=mat2_transposed,
        use_4x2_dim=is_woq_int4,
    )

    # TODO(jgong5): support dynamic shapes for n or k
    if has_free_symbols((n, k)):
        return False

    if isinstance(mat2, ir.BaseView):
        mat2 = mat2.unwrap_view()

    output_dtype, _ = get_gemm_template_output_and_compute_dtype(mat1.get_dtype())
    micro_gemm = create_micro_gemm(
        "micro_gemm",
        m,
        n,
        k,
        input_dtype=mat1.get_dtype(),
        input2_dtype=mat2.get_dtype(),
        output_dtype=output_dtype,
        num_threads=parallel_num_threads(),
        use_ref=not is_woq_int4,
        q_group_size=q_group_size,
    )

    def is_last_dim_stride1(x: IRNode) -> bool:
        x.freeze_layout()
        return x.get_stride()[-1] == 1

    return (
        layout.dtype in layout_dtypes
        and micro_gemm is not None
        and is_last_dim_stride1(mat1)  # TODO(jgong5): support transposed input
        and isinstance(mat2, ir.StorageBox)
        and (mat2.is_module_buffer() or not require_constant_mat2)
    )