def is_valid_mm_plus_mm(match: Match):
    if not (config.max_autotune or config.max_autotune_gemm):
        return False

    # Check if all required values exist
    mat1_val = match.kwargs["mat1"].meta.get("val")
    mat2_val = match.kwargs["mat2"].meta.get("val")
    mat3_val = match.kwargs["mat3"].meta.get("val")
    mat4_val = match.kwargs["mat4"].meta.get("val")

    if mat1_val is None or mat2_val is None or mat3_val is None or mat4_val is None:
        return False

    *_b1, m1, k1 = mat1_val.shape
    *_b2, k2, n1 = mat2_val.shape
    if k1 != k2:
        return False

    *_b1, m2, k3 = mat3_val.shape
    *_b2, k4, n2 = mat4_val.shape
    if k3 != k4:
        return False

    if m1 != m2 or n1 != n2:
        return False

    return True