def test_conversion(self):
        for cpu_tensor in [torch.randn((1, 2, 3, 4),
                                       dtype=torch.float, device=torch.device('cpu')),
                           torch.randn((1, 2, 3, 4, 5),
                                       dtype=torch.float, device=torch.device('cpu'))[:, :, :, :, 1]]:
            cpu_tensor.requires_grad_()
            convert_dtypes = {torch.half: [torch.half, torch.float],
                              torch.bfloat16: [torch.bfloat16, torch.float],
                              torch.float: [torch.bfloat16, torch.half]}
            # float/bfloat16/half cpu tensor to mkldnn tensortensor.
            for dtype1 in types:
                mkldnn_tensor = cpu_tensor.to_mkldnn(dtype1)
                self.assertEqual(mkldnn_tensor.dtype, dtype1)
                cpu_tensor_1 = mkldnn_tensor.to_dense()
                # not given dtype for to_dense, mkldnn tensor has same dtype with cpu tensor
                self.assertEqual(mkldnn_tensor.dtype, cpu_tensor_1.dtype)
                # mkldnn float/bfloat tensor to cpu float or bfloat tensor
                for dtype2 in convert_dtypes[dtype1]:
                    cpu_tensor_2 = mkldnn_tensor.to_dense(dtype2)
                    self.assertEqual(cpu_tensor_2.dtype, dtype2)
                    atol = 1e-5 if dtype1 == torch.float and dtype2 == torch.float else 1e-2
                    self.assertEqual(cpu_tensor, cpu_tensor_2.float(), atol=atol, rtol=0)

                self.assertEqual(mkldnn_tensor.device, torch.device('cpu'))
                self.assertEqual(mkldnn_tensor.size(), torch.Size([1, 2, 3, 4]))
                self.assertEqual(mkldnn_tensor.numel(), cpu_tensor.numel())
                if dtype1 == torch.float:
                    self.assertEqual(mkldnn_tensor.element_size(), cpu_tensor.element_size())
                else:
                    self.assertEqual(mkldnn_tensor.element_size(), cpu_tensor.element_size() / 2)
                self.assertRaisesRegex(RuntimeError,
                                       "Cannot access data pointer of Tensor that doesn't have storage",
                                       lambda: mkldnn_tensor.data_ptr() != 0)

            # bfloat cpu tensor to mkldnn float tensor or bfloat tensor.
            for orig_dtype in [torch.half, torch.bfloat16]:
                cpu_tensor_lower = cpu_tensor.to(dtype=orig_dtype)
                for dtype1 in convert_dtypes[orig_dtype]:
                    mkldnn_tensor = cpu_tensor_lower.to_mkldnn(dtype1)
                    self.assertEqual(mkldnn_tensor.dtype, dtype1)
                    cpu_tensor_1 = mkldnn_tensor.to_dense()
                    # not given dtype for to_dense, mkldnn tensor has same dtype with cpu tensor
                    self.assertEqual(mkldnn_tensor.dtype, cpu_tensor_1.dtype)
                    # mkldnn float/bfloat/half tensor to cpu float/bfloat/half tensor
                    for dtype2 in convert_dtypes[cpu_tensor_lower.dtype]:
                        cpu_tensor_2 = mkldnn_tensor.to_dense(dtype2)
                        self.assertEqual(cpu_tensor_2.dtype, dtype2)
                        self.assertEqual(cpu_tensor_lower,
                                         cpu_tensor_2.to(dtype=cpu_tensor_lower.dtype), atol=1e-5, rtol=0)

                    self.assertEqual(mkldnn_tensor.device, torch.device('cpu'))
                    self.assertEqual(mkldnn_tensor.size(), torch.Size([1, 2, 3, 4]))
                    self.assertEqual(mkldnn_tensor.numel(), cpu_tensor.numel())
                    if dtype1 in [torch.bfloat16, torch.half]:
                        self.assertEqual(mkldnn_tensor.element_size(), cpu_tensor_lower.element_size())
                    else:
                        self.assertEqual(mkldnn_tensor.element_size(), cpu_tensor_lower.element_size() * 2)
                    self.assertRaisesRegex(RuntimeError,
                                           "Cannot access data pointer of Tensor that doesn't have storage",
                                           lambda: mkldnn_tensor.data_ptr() != 0)