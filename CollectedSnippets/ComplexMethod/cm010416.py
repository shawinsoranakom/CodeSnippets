def _get_jiterator_fn(
    asm_str: str,
    constraints: str,
    n_inputs: int,
    input_dtype: torch.dtype,
    output_dtype: torch.dtype,
):
    from torch.cuda.jiterator import _create_jit_fn

    cuda_asm = _triton_asm_to_cuda_asm(asm_str)

    constraint_parts = [p.strip() for p in constraints.split(",")]
    output_constraints = [p.lstrip("=") for p in constraint_parts if p.startswith("=")]
    input_constraints = [p for p in constraint_parts if not p.startswith("=")]

    if input_dtype not in _DTYPE_TO_CUDA_TYPE:
        raise ValueError(f"Unsupported input dtype for inline asm: {input_dtype}")
    if output_dtype not in _DTYPE_TO_CUDA_TYPE:
        raise ValueError(f"Unsupported output dtype for inline asm: {output_dtype}")

    input_type = _DTYPE_TO_CUDA_TYPE[input_dtype]
    output_type = _DTYPE_TO_CUDA_TYPE[output_dtype]

    input_params = ", ".join(f"{input_type} in{i}" for i in range(n_inputs))
    out_constraints_str = ", ".join(f'"={c}"(result)' for c in output_constraints)
    in_constraints_str = ", ".join(
        f'"{c}"(in{i})' for i, c in enumerate(input_constraints)
    )
    escaped_asm = (
        cuda_asm.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
    )

    code = f"""
template <typename T>
{output_type} inline_asm_kernel({input_params}) {{
    {output_type} result;
    asm volatile (
        "{escaped_asm}"
        : {out_constraints_str}
        : {in_constraints_str}
    );
    return result;
}}
"""

    return _create_jit_fn(code)