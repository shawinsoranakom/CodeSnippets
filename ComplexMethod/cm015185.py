def _test_atleast_dim(self, torch_fn, np_fn, device, dtype):
        for ndims in range(5):
            shape = _rand_shape(ndims, min_size=5, max_size=10)
            for _ in range(ndims + 1):
                for with_extremal in [False, True]:
                    for contiguous in [False, True]:
                        # Generate Input.
                        x = _generate_input(shape, dtype, device, with_extremal)
                        if contiguous:
                            x = x.T
                        self.compare_with_numpy(
                            torch_fn, np_fn, x, device=None, dtype=None
                        )

                        # Compare sequence input
                        torch_sequence_x = (x,) * random.randint(3, 10)
                        np_sequence_x = tuple(
                            np.array(x.detach().cpu().numpy()) for x in torch_sequence_x
                        )
                        torch_res = torch_fn(*torch_sequence_x)
                        np_res = np_fn(*np_sequence_x)

                        torch_res = tuple(x.cpu() for x in torch_res)
                        np_res = tuple(torch.from_numpy(x) for x in np_res)
                        self.assertEqual(np_res, torch_res)