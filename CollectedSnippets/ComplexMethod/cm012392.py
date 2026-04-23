def grouped_mm_args(
    mat1: TensorBox,
    mat2: TensorBox,
    offs: TensorBox | None,
    layout=None,
    out_dtype=None,
):
    mat1, mat2 = realize_inputs(mat1, mat2)
    if offs is not None:
        realize_inputs(offs)
    mat1_size = mat1.get_size()
    mat2_size = mat2.get_size()

    m1dim, m2dim = len(mat1_size), len(mat2_size)

    assert m1dim == 2 or m1dim == 3
    assert m2dim == 2 or m2dim == 3

    if layout is None:
        from torch._inductor.ir import FixedLayout

        if out_dtype is None:
            out_dtype = mat1.get_dtype()
        alignment = 16 // out_dtype.itemsize

        if m1dim == 2:
            if m2dim == 2:
                assert offs is not None
                out_size = [offs.get_size()[0], mat1_size[0], mat2_size[1]]
            else:
                out_size = [mat1_size[0], mat2_size[-1]]
        else:
            if m2dim == 2:
                out_size = [mat1_size[1], mat2_size[1]]
            else:
                out_size = [mat1_size[0], mat1_size[1], mat2_size[-1]]
        size_padded = (out_size[-1] + alignment - 1) // alignment * alignment
        if len(out_size) == 2:
            out_stride = [size_padded, 1]
        else:
            out_stride = [out_size[1] * size_padded, size_padded, 1]

        layout = FixedLayout(
            mat1.get_device(),
            out_dtype,
            out_size,
            out_stride,
        )
    else:
        assert out_dtype is None, "out_dtype is ignored if layout is specified."

    return (mat1_size, mat2_size, layout, mat1, mat2, offs)