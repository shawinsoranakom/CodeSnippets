def helper(shape, alpha, op_name, inplace):
            if op_name == "add":
                op = torch.Tensor.add_ if inplace else torch.add
            elif op_name == "sub":
                op = torch.Tensor.sub_ if inplace else torch.sub

            for dtype in [torch.float16, torch.float32]:
                cpu_x = torch.randn(shape, device='cpu', dtype=dtype, requires_grad=False)
                mps_x = cpu_x.detach().clone().to('mps')

                cpu_y = torch.randn(shape, device='cpu', dtype=dtype, requires_grad=False)
                mps_y = cpu_y.detach().clone().to('mps')

                cpu_out = op(cpu_x, cpu_y, alpha=alpha)
                mps_out = op(mps_x, mps_y, alpha=alpha)
                # fp16 isn't accurate when alpha is passed
                # TODO: remove or fix 'tol' when we fix problems with fp16
                tol = 2e-3 if dtype is torch.float16 else None
                self.assertEqual(mps_out, cpu_out, rtol=tol, atol=tol)
                if not (cpu_y.shape != () and inplace):  # in-place output cannot be broadcasted.
                    # create a scalar tensor
                    cpu_s = torch.tensor(2.3, device='cpu', dtype=dtype, requires_grad=False)
                    mps_s = cpu_s.detach().clone().to('mps')
                    # primary tensor is scalar
                    self.assertEqual(op(cpu_s, cpu_y), op(mps_s, mps_y))
                # create a scalar tensor
                cpu_s = torch.tensor(2.3, device='cpu', dtype=dtype, requires_grad=False)
                mps_s = cpu_s.detach().clone().to('mps')
                # secondary tensor is scalar
                self.assertEqual(op(cpu_x, cpu_s), op(mps_x, mps_s), rtol=tol, atol=tol)