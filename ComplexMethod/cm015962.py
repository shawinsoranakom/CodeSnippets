def helper(n, c, h, w, d, kernel_size, stride=None):
            batch = n
            if not batch:
                batch = 1
            input = torch.randn(batch, c, d, h, w, dtype=dtype, device=device)
            input = input.contiguous(
                memory_format=torch.channels_last_3d
            ).requires_grad_()
            if not n:
                input = input.squeeze(0).detach().clone().requires_grad_()
            if isinstance(kernel_size, int):
                kernel_size = [kernel_size] * 3
            if stride is None:
                stride = kernel_size
            elif isinstance(stride, int):
                stride = [stride] * 3
            grad = torch.randn(
                batch,
                c,
                (d - kernel_size[0]) // stride[0] + 1,
                (h - kernel_size[1]) // stride[1] + 1,
                (w - kernel_size[2]) // stride[2] + 1,
                dtype=dtype,
                device=device,
            )
            grad = grad.contiguous(memory_format=torch.channels_last_3d)
            if not n:
                grad = grad.squeeze(0)
            pool = torch.nn.MaxPool3d(kernel_size, stride, return_indices=True).to(
                device
            )

            ref_input = input.detach().clone().contiguous().requires_grad_(True)
            ref_grad = grad.detach().clone().contiguous()
            ref_pool = torch.nn.MaxPool3d(kernel_size, stride, return_indices=True).to(
                device
            )
            out, ind = pool(input)
            out.backward(grad)
            ref_out, ref_ind = ref_pool(ref_input)
            ref_out.backward(ref_grad)

            if len(out.shape) == 4:
                self.assertTrue(
                    out.unsqueeze(0).is_contiguous(memory_format=torch.channels_last_3d)
                )
            else:
                self.assertTrue(out.is_contiguous(memory_format=torch.channels_last_3d))
            self.assertTrue(ref_out.is_contiguous())
            if len(ind.shape) == 4:
                self.assertTrue(
                    ind.unsqueeze(0).is_contiguous(memory_format=torch.channels_last_3d)
                )
            else:
                self.assertTrue(ind.is_contiguous(memory_format=torch.channels_last_3d))
            self.assertTrue(ref_ind.is_contiguous())
            self.assertEqual(out, ref_out)
            self.assertEqual(ind, ref_ind)
            if dtype == torch.half:
                self.assertEqual(input.grad, ref_input.grad, atol=0.05, rtol=0.01)
            else:
                self.assertEqual(input.grad, ref_input.grad)