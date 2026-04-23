def test_argminmax_multiple(self, device, dtype):
        # Case: All Ones
        t = torch.ones(3, 3, device=device, dtype=dtype)
        self.compare_with_numpy(torch.argmax, np.argmax, t)
        self.compare_with_numpy(torch.argmin, np.argmin, t)

        # Case: With single `nan` present.
        if dtype in floating_types_and(torch.half, torch.bfloat16):
            t[2, 2] = float('nan')
            self.compare_with_numpy(torch.argmax, np.argmax, t)
            self.compare_with_numpy(torch.argmin, np.argmin, t)

        # Case: Randomly Generated Tensors
        for ndims in range(1, 5):
            shape = _rand_shape(ndims, min_size=5, max_size=10)
            for with_extremal in [False, True]:
                for contiguous in [False, True]:
                    # Generate Input.
                    x = _generate_input(shape, dtype, device, with_extremal)

                    if dtype == torch.half:
                        max_val = torch.max(x.to(torch.float))
                        min_val = torch.min(x.to(torch.float))
                    else:
                        max_val = torch.max(x)
                        min_val = torch.min(x)

                    mask = torch.randn(x.shape) > 0.5
                    x[mask] = torch.tensor(max_val + 1, dtype=dtype)

                    mask = torch.randn(x.shape) > 0.5
                    x[mask] = torch.tensor(min_val - 1, dtype=dtype)

                    if not contiguous:
                        x = x.T

                    self.compare_with_numpy(torch.argmax, np.argmax, x, device=None, dtype=None)
                    self.compare_with_numpy(torch.argmin, np.argmin, x, device=None, dtype=None)

                    # Verify indices returned by max and min.
                    if dtype != torch.half:
                        rand_dim = random.randint(0, ndims - 1)
                        self.compare_with_numpy(lambda x: torch.max(x, dim=rand_dim)[1],
                                                lambda x: np.argmax(x, axis=rand_dim), x, device=None, dtype=None)
                        self.compare_with_numpy(lambda x: torch.min(x, dim=rand_dim)[1],
                                                lambda x: np.argmin(x, axis=rand_dim), x, device=None, dtype=None)

        def verify_against_numpy(t):
            # Argmax
            torch_fn = partial(torch.argmax, dim=1)
            np_fn = partial(np.argmax, axis=1)
            self.compare_with_numpy(torch_fn, np_fn, t)
            # Non-contiguous input
            self.compare_with_numpy(torch_fn, np_fn, t.T)

            # Verify indices returned by max.
            if dtype != torch.half:
                self.compare_with_numpy(lambda x: torch.max(x, dim=1)[1], np_fn, x, device=None, dtype=None)
                self.compare_with_numpy(lambda x: torch.max(x, dim=1)[1], np_fn, x.T, device=None, dtype=None)

            # Argmin
            torch_fn = partial(torch.argmin, dim=1)
            np_fn = partial(np.argmin, axis=1)
            self.compare_with_numpy(torch_fn, np_fn, t)
            # Non-contiguous input
            self.compare_with_numpy(torch_fn, np_fn, t.T)

            # Verify indices returned by min.
            if dtype != torch.half:
                self.compare_with_numpy(lambda x: torch.min(x, dim=1)[1], np_fn, x, device=None, dtype=None)
                self.compare_with_numpy(lambda x: torch.min(x, dim=1)[1], np_fn, x.T, device=None, dtype=None)

        # Case: Sample from issue: https://github.com/pytorch/pytorch/issues/41998
        t = torch.tensor([[1, 5],
                          [2, 10],
                          [3, 3]], device=device, dtype=dtype)
        verify_against_numpy(t)

        # Case: Sample from issue: https://github.com/pytorch/pytorch/issues/41998
        t = torch.tensor([[1, 5],
                          [2, 10],
                          [0, 0]], device=device, dtype=dtype)
        verify_against_numpy(t)