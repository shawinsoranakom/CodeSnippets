def test_lower_precision_accumulation_with_ref_path(self):
        # fix https://github.com/pytorch/pytorch/issues/95125
        # and https://github.com/pytorch/pytorch/issues/83863
        # for bf16 accumulation in gemm ref path
        def check_correctness(fn, dtype, *args):
            expected = fn(*args).to(dtype=dtype)
            with torch.backends.mkldnn.flags(enabled=False):
                def test():
                    lower_args = (arg.to(dtype=dtype) for arg in args)
                    tmp_result = fn(*lower_args)
                    return tmp_result
                c = test()
                if not (torch.all(c == expected)):
                    raise AssertionError(
                        f"Incorrect result with\nexpected: {expected}\ngot: {c}\n"
                    )
        # test matmul
        for dtype in [torch.bfloat16, torch.half]:
            for transa in [True, False]:
                for transb in [True, False]:
                    a = torch.ones(300, 300)
                    b = torch.ones(300, 300)
                    if transa:
                        a = a.transpose(0, 1).contiguous().transpose(0, 1)
                    if transb:
                        b = b.transpose(0, 1).contiguous().transpose(0, 1)
                    check_correctness(torch.matmul, dtype, a, b)
        # test bmm
        a = torch.ones(1, 1, 300)
        b = torch.ones(1, 300, 1)
        check_correctness(torch.bmm, torch.bfloat16, a, b)
        check_correctness(torch.bmm, torch.half, a, b)
        # test baddbmm
        a = torch.ones(1, 1, 300)
        b = torch.ones(1, 300, 1)
        c = torch.ones(1, 1, 1)
        check_correctness(torch.baddbmm, torch.bfloat16, c, a, b)
        check_correctness(torch.baddbmm, torch.half, c, a, b)
        # test mv/addmv
        for dtype in [torch.bfloat16, torch.half]:
            for trans in [True, False]:
                c = torch.ones(300) * -300
                a = torch.ones(300, 300)
                if trans:
                    a = a.transpose(0, 1).contiguous().transpose(0, 1)
                b = torch.ones(300)
                check_correctness(torch.mv, dtype, a, b)
                check_correctness(torch.addmv, dtype, c, a, b)
        # test dot
        a = torch.ones(300)
        b = torch.ones(300)
        check_correctness(torch.dot, torch.bfloat16, a, b)
        check_correctness(torch.dot, torch.half, a, b)