def test_transpose_vs_numpy(self, device, dtype):
        for fn in (torch.swapdims, torch.swapaxes, torch.transpose):
            for nd in range(5):
                shape = _rand_shape(nd, min_size=5, max_size=10)
                x = _generate_input(shape, dtype, device, with_extremal=False)
                for random_negative in [True, False]:
                    for src_dim, dst_dim in permutations(range(nd), r=2):
                        random_prob = random.random()

                        if random_negative and random_prob > 0.66:
                            src_dim = src_dim - nd
                        elif random_negative and random_prob > 0.33:
                            dst_dim = dst_dim - nd
                        elif random_negative:
                            src_dim = src_dim - nd
                            dst_dim = dst_dim - nd

                        partial_map = {
                            torch.swapdims: partial(
                                torch.swapdims, dim0=src_dim, dim1=dst_dim
                            ),
                            torch.swapaxes: partial(
                                torch.swapaxes, axis0=src_dim, axis1=dst_dim
                            ),
                            torch.transpose: partial(
                                torch.transpose, dim0=src_dim, dim1=dst_dim
                            ),
                        }

                        torch_fn = partial_map[fn]
                        np_fn = partial(np.swapaxes, axis1=src_dim, axis2=dst_dim)
                        self.compare_with_numpy(
                            torch_fn, np_fn, x, device=None, dtype=None
                        )

            # Move dim to same position
            x = torch.randn(2, 3, 5, 7, 11)
            partial_map = {
                torch.swapdims: partial(torch.swapdims, dim0=0, dim1=0),
                torch.swapaxes: partial(torch.swapaxes, axis0=0, axis1=0),
                torch.transpose: partial(torch.transpose, dim0=0, dim1=0),
            }
            torch_fn = partial_map[fn]
            np_fn = partial(np.swapaxes, axis1=0, axis2=0)
            self.compare_with_numpy(torch_fn, np_fn, x, device=None, dtype=None)