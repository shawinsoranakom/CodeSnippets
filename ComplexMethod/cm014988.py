def test_norm_matrix(self, device, dtype):
        make_arg = partial(make_tensor, dtype=dtype, device=device)

        def run_test_case(input, ord, dim, keepdim):
            msg = f'input.size()={input.size()}, ord={ord}, dim={dim}, keepdim={keepdim}, dtype={dtype}'
            result = torch.linalg.norm(input, ord, dim, keepdim)
            input_numpy = input.cpu().numpy()
            result_numpy = np.linalg.norm(input_numpy, ord, dim, keepdim)

            result = torch.linalg.norm(input, ord, dim, keepdim)
            self.assertEqual(result, result_numpy, msg=msg)
            if ord is not None and dim is not None:
                result = torch.linalg.matrix_norm(input, ord, dim, keepdim)
                self.assertEqual(result, result_numpy, msg=msg)

        ord_matrix = [1, -1, 2, -2, inf, -inf, 'nuc', 'fro']
        S = 10
        test_cases = [
            # input size, dim
            ((S, S), None),
            ((S, S), (0, 1)),
            ((S, S), (1, 0)),
            ((S, S, S, S), (2, 0)),
            ((S, S, S, S), (-1, -2)),
            ((S, S, S, S), (-1, -3)),
            ((S, S, S, S), (-3, 2)),
        ]

        for (shape, dim), keepdim, ord in product(test_cases, [True, False], ord_matrix):
            if ord in [2, -2, 'nuc']:
                # We need torch.svdvals
                if dtype == torch.float16 or dtype == torch.bfloat16:
                    continue
                # We need LAPACK or equivalent
                if ((torch.device(device).type == 'cuda' and not torch.cuda.has_magma and not has_cusolver()) or
                   (torch.device(device).type == 'cpu' and not torch._C.has_lapack)):
                    continue
            run_test_case(make_arg(shape), ord, dim, keepdim)