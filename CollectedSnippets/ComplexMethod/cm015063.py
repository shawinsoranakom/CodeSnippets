def reference(input, mat1, mat2, beta=1, alpha=1, left_alpha=None, right_alpha=None, op=op):
            if mat1.layout is not torch.strided:
                raise AssertionError(f"expected strided layout, got {mat1.layout}")
            if mat2.layout is not torch.strided:
                raise AssertionError(f"expected strided layout, got {mat2.layout}")
            if dtype is torch.int8:
                if op == '_int_bsr_dense_addmm':
                    mat12 = torch._int_mm(mat1, mat2)
                else:
                    # workaround RuntimeError: "addmm_cuda" not implemented for 'Char'
                    if out_dtype is not None:
                        mat12 = torch._int_mm(mat1, mat2).to(out_dtype)
                    else:
                        mat12 = torch._int_mm(mat1, mat2).to(torch.int8)
            else:
                mat12 = mat1 @ mat2
            if alpha != 1:
                mat12 *= alpha
            if left_alpha is not None:
                mat12 = left_alpha.reshape(*left_alpha.shape[:-1], -1, 1) * mat12
            if right_alpha is not None:
                mat12 = mat12 * right_alpha.reshape(*right_alpha.shape[:-1], 1, -1)
            return beta * input + mat12