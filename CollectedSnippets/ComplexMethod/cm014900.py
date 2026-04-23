def helper(shape, rounding_mode):
            for dtype in [torch.float32, torch.float16, torch.int32, torch.int64]:
                if ((rounding_mode is not None and "floor" in rounding_mode and dtype == torch.int64) or
                        (rounding_mode is not None and "trunc" in rounding_mode and dtype == torch.float16)) is False:
                    cpu_x = None
                    cpu_y = None
                    if (dtype in [torch.float32, torch.float16]):
                        cpu_x = torch.randn(shape, device='cpu', dtype=dtype, requires_grad=False)
                        cpu_y = torch.randn(shape, device='cpu', dtype=dtype, requires_grad=False)
                    else:
                        cpu_x = torch.randint(-10, 0, shape, device='cpu', dtype=dtype, requires_grad=False)
                        cpu_y = torch.randint(-10, 0, shape, device='cpu', dtype=dtype, requires_grad=False)

                    mps_x = cpu_x.detach().clone().to('mps')
                    # clamp to avoid division by 0
                    mps_y = cpu_y.detach().clone().to('mps')

                    if (rounding_mode == "floor_divide"):
                        result_div_cpu = torch.floor_divide(cpu_x, cpu_y)
                        result_div_mps = torch.floor_divide(mps_x, mps_y)
                        self.assertEqual(result_div_mps, result_div_cpu)
                    else:
                        result_div_cpu = torch.div(cpu_x, cpu_y, rounding_mode=rounding_mode)
                        result_div_mps = torch.div(mps_x, mps_y, rounding_mode=rounding_mode)
                        self.assertEqual(result_div_mps, result_div_cpu)