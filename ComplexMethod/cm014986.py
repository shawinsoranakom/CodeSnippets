def test_norm_dtype(self, device, dtype):
        make_arg = partial(make_tensor, dtype=dtype, device=device)

        def run_test_case(input_size, ord, keepdim, to_dtype):
            msg = (
                f'input_size={input_size}, ord={ord}, keepdim={keepdim}, '
                f'dtype={dtype}, to_dtype={to_dtype}')
            input = make_arg(input_size)
            result = torch.linalg.norm(input, ord, keepdim=keepdim)
            self.assertEqual(result.dtype, input.real.dtype, msg=msg)

            result_out = torch.empty((0), dtype=result.dtype, device=device)
            torch.linalg.norm(input, ord, keepdim=keepdim, out=result_out)
            self.assertEqual(result, result_out, msg=msg)

            result = torch.linalg.norm(input.to(to_dtype), ord, keepdim=keepdim)
            result_with_dtype = torch.linalg.norm(input, ord, keepdim=keepdim, dtype=to_dtype)
            self.assertEqual(result, result_with_dtype, msg=msg)

            result_out_with_dtype = torch.empty_like(result_with_dtype)
            torch.linalg.norm(input, ord, keepdim=keepdim, dtype=to_dtype, out=result_out_with_dtype)
            self.assertEqual(result_with_dtype, result_out_with_dtype, msg=msg)

        ord_vector = [0, 1, -1, 2, -2, 3, -3, 4.5, -4.5, inf, -inf, None]

        # In these orders we are computing the 10-th power and 10-th root of numbers.
        # We avoid them for half-precision types as it makes the tests above too badly conditioned
        if dtype != torch.float16 and dtype != torch.bfloat16:
            ord_vector.extend([0.1, -0.1])
        ord_matrix = ['fro', 'nuc', 1, -1, 2, -2, inf, -inf, None]
        S = 10

        if dtype == torch.cfloat:
            norm_dtypes = (torch.cfloat, torch.cdouble)
        elif dtype == torch.cdouble:
            norm_dtypes = (torch.cdouble,)
        elif dtype in (torch.float16, torch.bfloat16, torch.float):
            norm_dtypes = (torch.float, torch.double)
        elif dtype == torch.double:
            norm_dtypes = (torch.double,)
        else:
            raise RuntimeError("Unsupported dtype")

        for ord, keepdim, norm_dtype in product(ord_vector, (True, False), norm_dtypes):
            run_test_case((S,) , ord, keepdim, norm_dtype)

        for ord, keepdim, norm_dtype in product(ord_matrix, (True, False), norm_dtypes):
            if ord in [2, -2, 'nuc']:
                # We need torch.svdvals
                if dtype == torch.float16 or dtype == torch.bfloat16:
                    continue

                # We need LAPACK or equivalent
                if ((torch.device(device).type == 'cuda' and not torch.cuda.has_magma and not has_cusolver()) or
                   (torch.device(device).type == 'cpu' and not torch._C.has_lapack)):
                    continue
            run_test_case((S, S) , ord, keepdim, norm_dtype)