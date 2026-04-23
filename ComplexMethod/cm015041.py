def test_sparse_compressed_constructor(self, layout, device, dtype,
                                           use_factory_function, shape_and_device_inference, input_kind):
        if input_kind == 'list' and shape_and_device_inference:
            if torch.device(device).type == 'cuda':
                # list inputs to factory/constructor function without
                # specifying device will result a sparse compressed tensor
                # on CPU. So, skip testing against cuda device as unused.
                self.skipTest("nothing to test")
            if dtype not in {torch.float32, torch.complex64, torch.int64, torch.bool}:
                self.skipTest("dtype not supported with list values")

        expected_devices = [torch.device(device)]
        if TEST_CUDA and torch.device(device).type == 'cuda' and torch.cuda.device_count() >= 2 and not shape_and_device_inference:
            expected_devices.append(torch.device('cuda:1'))

        factory_function = {
            torch.sparse_csr: torch.sparse_csr_tensor,
            torch.sparse_csc: torch.sparse_csc_tensor,
            torch.sparse_bsr: torch.sparse_bsr_tensor,
            torch.sparse_bsc: torch.sparse_bsc_tensor,
        }[layout]
        compressed_indices_mth, plain_indices_mth = sparse_compressed_indices_methods[layout]
        if input_kind == 'list':
            index_dtypes = [torch.int64]
        else:
            index_dtypes = [torch.int32, torch.int64]
        if dtype.is_floating_point or dtype.is_complex:
            requires_grad_lst = [False, True]
        else:
            requires_grad_lst = [False]
        for index_dtype in index_dtypes:
            for expected_device in expected_devices:
                for (compressed_indices, plain_indices, values), kwargs in self.generate_simple_inputs(
                        layout, device=expected_device, dtype=dtype, index_dtype=index_dtype,
                        # skip zero-sized tensors for list inputs:
                        enable_zero_sized=input_kind != 'list',
                        output_tensor=False):
                    size = kwargs['size']
                    if shape_and_device_inference and 0 in size:
                        # skip shape inference for zero-sized tensor
                        # inputs because (i) the shape determined from
                        # an empty list is ambiguous, and (ii) the
                        # size of the plain dimension defined as
                        # max(plain_indices) is undefined if
                        # plain_indices has no values
                        continue
                    compressed_indices_expect = compressed_indices
                    plain_indices_expect = plain_indices
                    values_expect = values

                    if input_kind == 'list':
                        compressed_indices = compressed_indices.tolist()
                        plain_indices = plain_indices.tolist()
                        values = values.tolist()

                    for requires_grad in requires_grad_lst:
                        if use_factory_function:
                            if shape_and_device_inference:
                                sparse = factory_function(
                                    compressed_indices, plain_indices, values, requires_grad=requires_grad)
                            else:
                                sparse = factory_function(
                                    compressed_indices, plain_indices, values, size,
                                    dtype=dtype, device=expected_device, requires_grad=requires_grad)
                        else:
                            if shape_and_device_inference:
                                sparse = torch.sparse_compressed_tensor(
                                    compressed_indices, plain_indices, values,
                                    layout=layout, requires_grad=requires_grad)
                            else:
                                sparse = torch.sparse_compressed_tensor(
                                    compressed_indices, plain_indices, values, size,
                                    dtype=dtype, layout=layout, device=expected_device, requires_grad=requires_grad)

                        self.assertEqual(layout, sparse.layout)
                        self.assertEqual(size, sparse.shape)
                        self.assertEqual(compressed_indices_expect, compressed_indices_mth(sparse))
                        self.assertEqual(plain_indices_expect, plain_indices_mth(sparse))
                        self.assertEqual(values_expect, sparse.values())
                        self.assertEqual(sparse.device, sparse.values().device)
                        self.assertEqual(sparse.device, expected_device)
                        self.assertEqual(sparse.values().requires_grad, requires_grad)
                        self.assertEqual(sparse.requires_grad, requires_grad)
                        self.assertFalse(compressed_indices_mth(sparse).requires_grad)
                        self.assertFalse(plain_indices_mth(sparse).requires_grad)