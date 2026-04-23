def test_dirac_identity(self):
        for groups in [1, 3]:
            batch, in_c, out_c, size, kernel_size = (
                8,
                3,
                9,
                5,
                3,
            )  # in_c, out_c must divide by groups
            eff_out_c = out_c // groups

            # Test 1D
            input_var = torch.randn(batch, in_c, size)
            filter_var = torch.zeros(eff_out_c, in_c, kernel_size)
            filter_var = torch.cat([filter_var] * groups)
            init.dirac_(filter_var, groups)
            output_var = F.conv1d(input_var, filter_var)
            input_tensor, output_tensor = (
                input_var.data,
                output_var.data,
            )  # Variables do not support nonzero
            for g in range(groups):
                # Assert in_c outputs are preserved (per each group)
                self.assertEqual(
                    input_tensor[:, :, 1:-1],
                    output_tensor[:, eff_out_c * g : eff_out_c * g + in_c, :],
                )
                # Assert extra outputs are 0
                if (
                    torch.nonzero(
                        output_tensor[:, eff_out_c * g + in_c : eff_out_c * (g + 1), :]
                    ).numel()
                    != 0
                ):
                    raise AssertionError("Expected extra outputs to be 0")

            # Test 2D
            input_var = torch.randn(batch, in_c, size, size)
            filter_var = torch.zeros(eff_out_c, in_c, kernel_size, kernel_size)
            filter_var = torch.cat([filter_var] * groups)
            init.dirac_(filter_var, groups)
            output_var = F.conv2d(input_var, filter_var)
            input_tensor, output_tensor = (
                input_var.data,
                output_var.data,
            )  # Variables do not support nonzero
            for g in range(groups):
                # Assert in_c outputs are preserved (per each group)
                self.assertEqual(
                    input_tensor[:, :, 1:-1, 1:-1],
                    output_tensor[:, eff_out_c * g : eff_out_c * g + in_c, :, :],
                )
                # Assert extra outputs are 0
                if (
                    torch.nonzero(
                        output_tensor[
                            :, eff_out_c * g + in_c : eff_out_c * (g + 1), :, :
                        ]
                    ).numel()
                    != 0
                ):
                    raise AssertionError("Expected extra outputs to be 0")

            # Test 3D
            input_var = torch.randn(batch, in_c, size, size, size)
            filter_var = torch.zeros(
                eff_out_c, in_c, kernel_size, kernel_size, kernel_size
            )
            filter_var = torch.cat([filter_var] * groups)
            init.dirac_(filter_var, groups)
            output_var = F.conv3d(input_var, filter_var)
            input_tensor, output_tensor = input_var.data, output_var.data
            for g in range(groups):
                # Assert in_c outputs are preserved (per each group)
                self.assertEqual(
                    input_tensor[:, :, 1:-1, 1:-1, 1:-1],
                    output_tensor[:, eff_out_c * g : eff_out_c * g + in_c, :, :, :],
                )
                # Assert extra outputs are 0
                if (
                    torch.nonzero(
                        output_tensor[
                            :, eff_out_c * g + in_c : eff_out_c * (g + 1), :, :, :
                        ]
                    ).numel()
                    != 0
                ):
                    raise AssertionError("Expected extra outputs to be 0")