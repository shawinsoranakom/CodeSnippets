def run_test_case(input, ord, dim, keepdim, should_error):
            msg = f'input.size()={input.size()}, ord={ord}, dim={dim}, keepdim={keepdim}, dtype={dtype}'
            input_numpy = input.cpu().numpy()
            ops = [torch.linalg.norm]

            if ord is not None and dim is not None:
                ops.append(torch.linalg.matrix_norm)

            if should_error == 'both':
                with self.assertRaises(ValueError):
                    np.linalg.norm(input_numpy, ord, dim, keepdim)
                for op in ops:
                    with self.assertRaises(IndexError):
                        op(input, ord, dim, keepdim)
            elif should_error == 'np_only':
                with self.assertRaises(ValueError):
                    np.linalg.norm(input_numpy, ord, dim, keepdim)
                for op in ops:
                    result = op(input, ord, dim, keepdim)
                    dim_ = dim
                    if dim_ is None:
                        dim_ = (0, 1)
                    expected_shape = list(input.shape)
                    if keepdim:
                        expected_shape[dim_[0]] = 1
                        expected_shape[dim_[1]] = 1
                    else:
                        del expected_shape[max(dim_)]
                        del expected_shape[min(dim_)]
                    expected = torch.zeros(expected_shape, dtype=dtype.to_real())
                    self.assertEqual(expected, result, msg=msg)
            else:
                result_numpy = np.linalg.norm(input_numpy, ord, dim, keepdim)
                for op in ops:
                    result = op(input, ord, dim, keepdim)
                    self.assertEqual(result, result_numpy, msg=msg)