def test_group_norm(self):
        # hypothesis is flaky for this test, create test cases manually
        batches_list = (1, 7)
        num_groups_list = (1, 4)
        channels_per_groups = (1, 36, 72)
        elements_per_channels = (8, 128, 1024)
        torch_types = (torch.qint8, torch.quint8)
        y_scales = (0.1, 4.23)
        y_zero_points = (0, 1)
        channels_last_list = [True, False]
        affine_list = [True, False]
        combined = [batches_list, num_groups_list, channels_per_groups, elements_per_channels,
                    torch_types, y_scales, y_zero_points, channels_last_list, affine_list]
        test_cases = itertools.product(*combined)

        with override_quantized_engine("fbgemm"):
            for test_case in test_cases:

                batches, num_groups, channels_per_group, elements_per_channel, \
                    torch_type, Y_scale, Y_zero_point, channels_last, \
                    affine = test_case
                num_channels = num_groups * channels_per_group
                # minimum rank for channels_last
                shapes = (batches, num_channels, elements_per_channel, 1)

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

                # Initialize the weights non-randomly for reproducibility
                if affine:
                    weight = torch.ones(num_channels).float() * 0.5
                    bias = torch.ones(num_channels).float()
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
                for batch_idx in range(batches):
                    for group_idx in range(num_groups):
                        ch_start = group_idx * channels_per_group
                        ch_end = ch_start + channels_per_group
                        group_vals = dqX[batch_idx][ch_start:ch_end]
                        assume(
                            float(torch.unique(group_vals).shape[0]) / group_vals.numel() > 0.001
                            or group_vals.numel() < 5)

                qY = torch.ops.quantized.group_norm(qX, num_groups, weight, bias, eps, Y_scale, Y_zero_point)

                dqY_hat = F.group_norm(dqX, num_groups=num_groups, weight=weight, bias=bias, eps=eps)
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