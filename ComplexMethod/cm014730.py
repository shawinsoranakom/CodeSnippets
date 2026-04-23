def test_batchnorm_nhwc_cpu(self):
        def helper(self, mod, size, dtype, mixed_dtype=False, format=torch.channels_last, precision=None):
            channels = size[1]
            input = torch.randn(size, dtype=dtype, device='cpu', requires_grad=True)
            input = input.contiguous(memory_format=format).to(dtype)
            input.retain_grad()
            grad = torch.randn(size, dtype=dtype, device='cpu')
            grad = grad.contiguous(memory_format=format)
            bn = mod(channels).cpu().to(dtype)
            bn.weight.data.uniform_()
            bn.bias.data.uniform_()

            ref_input = input.detach().clone().contiguous().requires_grad_(True)
            ref_grad = grad.detach().clone().contiguous()
            ref_bn = mod(channels).cpu().to(dtype)
            ref_bn.load_state_dict(bn.state_dict())

            if mixed_dtype:
                bn.float()
                ref_bn.float()

            out = bn(input)
            out.backward(grad)
            ref_out = ref_bn(ref_input)
            ref_out.backward(ref_grad)

            self.assertTrue(out.is_contiguous(memory_format=format))
            self.assertTrue(ref_out.is_contiguous())
            self.assertEqual(out, ref_out)
            self.assertEqual(bn.weight.grad, ref_bn.weight.grad, atol=precision, rtol=precision)
            self.assertEqual(bn.bias.grad, ref_bn.bias.grad)
            self.assertEqual(input.grad, ref_input.grad)

        # test NC11 and N1HW; test mixed dtype
        for shape in [(4, 8, 10, 10), (4, 1, 9, 9), (4, 9, 1, 1)]:
            for dtype in [torch.float, torch.bfloat16, torch.float16]:
                for mixed_dtype in [False, True]:
                    if dtype == torch.float:
                        mixed_dtype = False
                    helper(self, nn.BatchNorm2d, shape, dtype, mixed_dtype, torch.channels_last)

        precisons = {torch.float: 1e-4, torch.bfloat16: 1e-4, torch.float16: None}
        for shape in [(4, 8, 2, 10, 10), (4, 1, 2, 9, 9), (4, 9, 1, 1, 1)]:
            for dtype in [torch.float, torch.bfloat16, torch.float16]:
                for mixed_dtype in [False, True]:
                    if dtype == torch.float:
                        mixed_dtype = False
                    helper(self, nn.BatchNorm3d, shape, dtype, mixed_dtype, torch.channels_last_3d, precisons[dtype])