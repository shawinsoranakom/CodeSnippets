def _compare_std_var_with_numpy(self, op, device, dtype, input, dim,
                                    keepdim, unbiased, use_out):
        a = input.cpu().numpy() if input.dtype is not torch.bfloat16 else input.float().cpu().numpy()
        numpy_kwargs = {
            'axis' : dim,
            'keepdims' : keepdim,
            'ddof' : 1 if unbiased else 0,
        }

        if dim is None:
            del numpy_kwargs['axis']
            del numpy_kwargs['keepdims']

        if op == 'var':
            torch_op = torch.var
            numpy_op = np.var
        elif op == 'std':
            torch_op = torch.std
            numpy_op = np.std
        else:
            self.fail("Unknown op!")

        numpy_result = numpy_op(a, **numpy_kwargs)

        if dim is None and use_out is False:
            torch_result = torch_op(input, unbiased)
        elif dim is not None and use_out is False:
            torch_result = torch_op(input, dim, unbiased, keepdim)
        elif dim is not None and use_out is True:
            out = torch.empty(0, device=device, dtype=dtype)
            torch_result = torch_op(input, dim, unbiased, keepdim, out=out)
        else:
            out = torch.empty(0, device=device, dtype=dtype)
            torch_result = torch_op(input, dim, unbiased, keepdim, out=out)

        exact_dtype = input.dtype not in (torch.bfloat16, torch.complex32, torch.complex64, torch.complex128)
        self.assertEqual(torch_result, numpy_result, exact_dtype=exact_dtype)