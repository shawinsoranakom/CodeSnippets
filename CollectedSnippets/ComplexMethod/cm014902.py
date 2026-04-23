def helper(shape, dtype=torch.float, contiguous=True):
            cpu_x = torch.randn(shape, device='cpu', dtype=dtype)
            x = cpu_x.detach().clone().to('mps')

            if not contiguous and (0 not in shape and len(shape) >= 2):
                # Transposing will make the tensor non-contiguous
                cpu_x = cpu_x.transpose(0, 1)
                x = x.transpose(0, 1)
                if x.is_contiguous():
                    raise AssertionError("expected non-contiguous tensor")

            cpu_x.requires_grad_()
            x.requires_grad_()

            mish_result = torch.nn.Mish()(x)
            mish_result_cpu = torch.nn.Mish()(cpu_x)

            cpu_grad = torch.ones_like(mish_result_cpu)
            grad = cpu_grad.to('mps')

            mish_result.backward(gradient=grad)
            mish_result_cpu.backward(gradient=cpu_grad)

            atol = 1e-5 if dtype == torch.float else 1e-2
            rtol = 1e-3 if dtype == torch.float else 1e-2
            self.assertEqual(mish_result, mish_result_cpu.to(dtype), atol=atol, rtol=rtol)

            if x.grad is None:
                raise AssertionError("expected x.grad to be populated")
            self.assertEqual(x.grad, cpu_x.grad, atol=atol, rtol=rtol)