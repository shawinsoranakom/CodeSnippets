def run_test(matsize, batchdims, mat_chars):
            num_matrices = reduce(operator.mul, batchdims, 1)
            list_of_matrices = []

            for idx in range(num_matrices):
                mat_type = idx % len(mat_chars)
                if mat_chars[mat_type] == 'sym':
                    list_of_matrices.append(random_symmetric_matrix(matsize, dtype=dtype, device=device))
                elif mat_chars[mat_type] == 'sym_psd':
                    list_of_matrices.append(random_symmetric_psd_matrix(matsize, dtype=dtype, device=device))
                elif mat_chars[mat_type] == 'sym_pd':
                    list_of_matrices.append(random_symmetric_pd_matrix(matsize, dtype=dtype, device=device))
                elif mat_chars[mat_type] == 'sing':
                    list_of_matrices.append(torch.ones(matsize, matsize, dtype=dtype, device=device))
                elif mat_chars[mat_type] == 'non_sing':
                    list_of_matrices.append(random_square_matrix_of_rank(matsize, matsize, dtype=dtype, device=device))
            full_tensor = torch.stack(list_of_matrices, dim=0).reshape(batchdims + (matsize, matsize))
            # Scaling adapted from `get_random_mat_scale` in _test_det_logdet_slogdet
            full_tensor *= (math.factorial(matsize - 1) ** (-1.0 / (2 * matsize)))

            for fn in [torch.det, torch.logdet, torch.slogdet, torch.linalg.slogdet]:
                expected_value = []
                actual_value = fn(full_tensor)
                for full_idx in itertools.product(*(list(range(x)) for x in batchdims)):
                    expected_value.append(fn(full_tensor[full_idx]))

                if fn == torch.slogdet or fn == torch.linalg.slogdet:
                    sign_value = torch.stack([tup[0] for tup in expected_value], dim=0).reshape(batchdims)
                    expected_value = torch.stack([tup[1] for tup in expected_value], dim=0).reshape(batchdims)
                    self.assertEqual(sign_value, actual_value[0])
                    self.assertEqual(expected_value, actual_value[1])
                else:
                    expected_value = torch.stack(expected_value, dim=0).reshape(batchdims)
                    self.assertEqual(actual_value, expected_value)