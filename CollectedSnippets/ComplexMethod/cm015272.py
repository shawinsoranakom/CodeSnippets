def test_adaptive_avg_pool(self):

        side_lens = (range(1, 10))
        dim_lens = (range(3, 5))
        torch_type = torch.qint8
        zero_points = (0, 1)
        combined = [side_lens, dim_lens, zero_points]
        test_cases = itertools.product(*combined)
        for test_case in test_cases:
            output_size_d = random.randint(1, 10)
            output_size_h = random.randint(1, 10)
            output_size_w = random.randint(1, 10)
            side_len, dim_len, zero_point = test_case
            shapes = [side_len] * dim_len
            X, X_scale, X_zero_point = \
                _get_random_tensor_and_q_params(shapes, 1.0, zero_point)
            X = np.array(X)
            scale = 1
            ndim = X.ndim
            dim_to_check = []
            if ndim <= 4:
                dim_to_check.append(2)
            if ndim >= 4:
                dim_to_check.append(3)

            D, H, W = X.shape[-3:]
            output_size_d = min(output_size_d, D)
            output_size_h = min(output_size_h, H)
            output_size_w = min(output_size_w, W)

            X = torch.from_numpy(X)
            qX = torch.quantize_per_tensor(X, scale=scale, zero_point=zero_point,
                                           dtype=torch_type)

            for dim in dim_to_check:
                if dim == 2:
                    if output_size_h == output_size_w:
                        output_size = output_size_h
                    else:
                        output_size = (output_size_h, output_size_w)
                elif dim == 3:
                    if output_size_d == output_size_h == output_size_w:
                        output_size = output_size_h
                    else:
                        output_size = (output_size_d, output_size_h, output_size_w)

                # Run reference on int_repr + round to avoid double rounding error.
                ref_op = getattr(torch.nn.functional, f'adaptive_avg_pool{dim}d')
                X_ref = ref_op(qX.int_repr().to(torch.float), output_size).round()

                ops_under_test = {
                    "nn.functional":
                        getattr(torch.nn.functional, f'adaptive_avg_pool{dim}d'),
                    "nn.quantized.functional":
                        getattr(torch.ao.nn.quantized.functional, f'adaptive_avg_pool{dim}d'),
                    "ao.nn.quantized.functional":
                        getattr(torch.ao.nn.quantized.functional, f'adaptive_avg_pool{dim}d')
                }

                error_message = r"Results are off for {}:\n\tExpected:\n{}\n\tGot:\n{}"

                for name, op in ops_under_test.items():
                    # TODO: torch.cuda.is_available() should be swapped for a flag that checks if cudnn
                    # is enabled in the build when cudnn supports adaptive average pooling
                    devices = ["cpu", "cuda"] if (dim == 2 and torch.cuda.is_available()) else ["cpu"]
                    for device in devices:
                        qX_hat = op(qX.to(device=device), output_size=output_size)
                        self.assertEqual(
                            X_ref, qX_hat.int_repr(), atol=1.0,
                            rtol=0, msg=error_message.format(name, X_ref, qX_hat), exact_dtype=False)
                        self.assertEqual(
                            scale, qX_hat.q_scale(),
                            msg=error_message.format(name + '.scale', scale,
                                                     qX_hat.q_scale()))
                        self.assertEqual(
                            zero_point, qX_hat.q_zero_point(),
                            msg=error_message.format(name + '.zero_point', scale,
                                                     qX_hat.q_zero_point()))