def test_instance_norm(self):
        max_sides = (4, 5)
        shape_list = ([2, 2, 2, 2], [8, 8, 8, 8], [11, 11, 11, 11])
        torch_types = (torch.qint8, torch.quint8)
        y_scales = (0.1, 4.23)
        y_zero_points = (0, 1)
        channels_last_list = (True, False)
        affine_list = (True, False)
        combined = [shape_list, torch_types, y_scales, y_zero_points, channels_last_list, affine_list]
        test_cases_product = itertools.product(*combined)
        test_cases = list(test_cases_product)
        # NB: Add just one test case to test overflow, but this case is too slow to run
        # internally in @fbcode//mode/dev, the long pole is the 4x calls to torch.sort
        # inside torch.unique current implementation
        if not IS_SANDCASTLE:
            test_cases.append([
                [1, 4, 224, 224, 160],  # shape,
                torch.qint8,  # torch_type
                0.1,  # scale
                0,  # zero_point
                False,   # channels_last
                True,  # affine
            ])
        with override_quantized_engine("fbgemm"):
            for test_case in test_cases:

                shapes, torch_type, Y_scale, Y_zero_point, channels_last, affine = test_case
                if channels_last and shapes.__len__() >= 5:
                    # required rank 4 tensor to use channels_last format
                    continue

                # In the FP kernel, sums and sums of squares are calculated in floating point.
                # In the int8 and uint8 versions of the quantized kernel, they are
                # calculated in integer arithmetic (which is exact).
                # Because of this, the numerics do not always match exactly which is
                # expected and acceptable. We do the following to allow this failure
                # in this test:
                # 1. do not use Hypothesis to generate the input tensor.  Hypothesis
                #    favors homogeneous inputs in its search strategies which isn't
                #    representative of the inputs we care about, and tends to maximize
                #    this particular numerics difference.
                # 2. allow a small % of off by Y_scale errors.  Even when the
                #    variance of the input is high, there can be off by one errors
                #    in the result if the input value happens to fall exactly on
                #    the bin boundary of the output scale.
                #
                # If we want the numerics to match we could switch to calculating
                # mean+var in floating point in the future, at the cost of speed.
                X, X_scale, X_zero_point = \
                    _get_random_tensor_and_q_params(shapes, 1.0, torch_type)

                num_channels = shapes[1]
                if affine:
                    weight = torch.rand(num_channels).float() * 0.5
                    bias = torch.rand(num_channels).float()
                    for i in range(num_channels):
                        weight[i] *= i
                        bias[i] *= i
                else:
                    weight = None
                    bias = None
                eps = 0.001

                qX = torch.quantize_per_tensor(X, X_scale, X_zero_point, torch_type)
                if channels_last:
                    qX = qX.contiguous(memory_format=torch.channels_last)
                dqX = qX.dequantize()

                # Enforce non-homogeneous inputs
                batches = shapes[0]
                for batch_idx in range(batches):
                    for ch_idx in range(num_channels):
                        ch_vals = dqX[batch_idx][ch_idx]
                        assume(
                            float(torch.unique(ch_vals).shape[0]) / ch_vals.numel() > 0.01
                            or ch_vals.numel() < 5 or ch_vals.numel() > 25600)

                qY = torch.ops.quantized.instance_norm(qX, weight, bias, eps, Y_scale, Y_zero_point)

                dqY_hat = F.instance_norm(dqX, weight=weight, bias=bias, eps=eps)
                qY_hat = torch.quantize_per_tensor(dqY_hat, Y_scale, Y_zero_point, torch_type)

                # Due to the numerics difference mentioned above between calculating
                # the variance in float vs int, the results can still be slightly
                # different.
                dqY = qY.dequantize()
                dqY_hat = qY_hat.dequantize()
                diff = dqY - dqY_hat

                # off-by-one errors are magnitude of Y_scale
                num_diff = torch.sum(diff > Y_scale * 1.0001)
                pct_diff = float(num_diff) / (diff.numel() + 1e-5)
                num_diff_off_by_one = torch.sum((diff > 0) * (diff <= Y_scale))
                pct_diff_off_by_one = float(num_diff_off_by_one) / (diff.numel() + 1e-5)

                self.assertTrue(pct_diff < 1e-6)
                self.assertTrue(pct_diff_off_by_one < 0.01)