def test_factory(self, device, dtype):
        for test_empty_tensor in [True, False]:
            if test_empty_tensor:
                default_size = torch.Size([1, 3, 0])
                size = torch.Size([3, 3, 0])
            else:
                default_size = torch.Size([1, 3])
                size = torch.Size([3, 3])
            for include_size in [True, False]:
                for use_tensor_idx in [True, False]:
                    for use_tensor_val in [True, False]:
                        for use_cuda in ([False] if not torch.cuda.is_available() else [True, False]):
                            # have to include size with cuda sparse tensors
                            include_size = include_size or use_cuda
                            long_dtype = torch.int64
                            device = torch.device('cpu') if not use_cuda else \
                                torch.device(torch.cuda.device_count() - 1)
                            indices = torch.tensor(([0], [2]), dtype=long_dtype) if use_tensor_idx else ([0], [2])
                            if test_empty_tensor:
                                values = torch.empty(1, 0).to(dtype)
                            else:
                                if use_tensor_val:
                                    values = torch.tensor([1.], dtype=dtype)
                                else:
                                    values = 1.
                            if include_size:
                                sparse_tensor = torch.sparse_coo_tensor(indices, values, size, dtype=dtype,
                                                                        device=device, requires_grad=True)
                            else:
                                sparse_tensor = torch.sparse_coo_tensor(indices, values, dtype=dtype,
                                                                        device=device, requires_grad=True)
                            self.assertEqual(indices, sparse_tensor._indices())
                            self.assertEqual(values, sparse_tensor._values())
                            self.assertEqual(size if include_size else default_size, sparse_tensor.size())
                            self.assertEqual(dtype, sparse_tensor.dtype)
                            if use_cuda:
                                self.assertEqual(device, sparse_tensor._values().device)
                            self.assertEqual(True, sparse_tensor.requires_grad)