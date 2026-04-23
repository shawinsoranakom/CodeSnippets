def _test_special_stacks(self, dim, at_least_dim, torch_fn, np_fn, device, dtype):
        # Test error for non-tuple argument
        t = torch.randn(10)
        with self.assertRaisesRegex(TypeError, "must be tuple of Tensors, not Tensor"):
            torch_fn(t)
        # Test error for a single array
        with self.assertRaisesRegex(TypeError, "must be tuple of Tensors, not Tensor"):
            torch_fn(t)

        # Test 0-D
        num_tensors = random.randint(1, 5)
        input_t = [torch.tensor(random.uniform(0, 10), device=device, dtype=dtype) for i in range(num_tensors)]
        actual = torch_fn(input_t)
        expected = np_fn([input.cpu().numpy() for input in input_t])
        self.assertEqual(actual, expected)

        for ndims in range(1, 5):
            base_shape = list(_rand_shape(ndims, min_size=1, max_size=5))
            for i in range(ndims):
                shape = list(base_shape)
                num_tensors = random.randint(1, 5)
                torch_input = []
                # Create tensors with shape being different along one axis only
                for _ in range(num_tensors):
                    shape[i] = random.randint(1, 5)
                    torch_input.append(_generate_input(tuple(shape), dtype, device, with_extremal=False))

                # Determine if input tensors have valid dimensions.
                valid_dim = True
                for k in range(len(torch_input) - 1):
                    for tdim in range(ndims):
                        # Test whether all tensors have the same shape except in concatenating dimension
                        # Unless the number of dimensions is less than the corresponding at_least function dimension
                        # Since the original concatenating dimension would shift after applying at_least and would no
                        # longer be the concatenating dimension
                        if (ndims < at_least_dim or tdim != dim) and torch_input[k].size()[tdim] != torch_input[k + 1].size()[tdim]:
                            valid_dim = False

                # Special case for hstack is needed since hstack works differently when ndims is 1
                if valid_dim or (torch_fn is torch.hstack and ndims == 1):
                    # Valid dimensions, test against numpy
                    np_input = [input.cpu().numpy() for input in torch_input]
                    actual = torch_fn(torch_input)
                    expected = np_fn(np_input)
                    self.assertEqual(actual, expected)
                else:
                    # Invalid dimensions, test for error
                    with self.assertRaisesRegex(RuntimeError, "Sizes of tensors must match except in dimension"):
                        torch_fn(torch_input)
                    with self.assertRaises(ValueError):
                        np_input = [input.cpu().numpy() for input in torch_input]
                        np_fn(np_input)