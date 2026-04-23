def test_movedim(self, device, dtype):
        for fn in [torch.moveaxis, torch.movedim]:
            for nd in range(5):
                shape = self._rand_shape(nd, min_size=5, max_size=10)
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

                        # Integer `source` and `destination`
                        torch_fn = partial(fn, source=src_dim, destination=dst_dim)
                        np_fn = partial(
                            np.moveaxis, source=src_dim, destination=dst_dim
                        )
                        self.compare_with_numpy(
                            torch_fn, np_fn, x, device=None, dtype=None
                        )

                    if nd == 0:
                        continue

                    def make_index_negative(sequence, idx):
                        sequence = list(sequence)
                        sequence[random_idx] = sequence[random_idx] - nd
                        return tuple(src_sequence)

                    for src_sequence in permutations(
                        range(nd), r=random.randint(1, nd)
                    ):
                        # Sequence `source` and `destination`
                        dst_sequence = tuple(
                            random.sample(range(nd), len(src_sequence))
                        )

                        # Randomly change a dim to a negative dim representation of itself.
                        random_prob = random.random()
                        if random_negative and random_prob > 0.66:
                            random_idx = random.randint(0, len(src_sequence) - 1)
                            src_sequence = make_index_negative(src_sequence, random_idx)
                        elif random_negative and random_prob > 0.33:
                            random_idx = random.randint(0, len(src_sequence) - 1)
                            dst_sequence = make_index_negative(dst_sequence, random_idx)
                        elif random_negative:
                            random_idx = random.randint(0, len(src_sequence) - 1)
                            dst_sequence = make_index_negative(dst_sequence, random_idx)
                            random_idx = random.randint(0, len(src_sequence) - 1)
                            src_sequence = make_index_negative(src_sequence, random_idx)

                        torch_fn = partial(
                            fn, source=src_sequence, destination=dst_sequence
                        )
                        np_fn = partial(
                            np.moveaxis, source=src_sequence, destination=dst_sequence
                        )
                        self.compare_with_numpy(
                            torch_fn, np_fn, x, device=None, dtype=None
                        )

            # Move dim to same position
            x = torch.randn(2, 3, 5, 7, 11)
            torch_fn = partial(fn, source=(0, 1), destination=(0, 1))
            np_fn = partial(np.moveaxis, source=(0, 1), destination=(0, 1))
            self.compare_with_numpy(torch_fn, np_fn, x, device=None, dtype=None)

            torch_fn = partial(fn, source=1, destination=1)
            np_fn = partial(np.moveaxis, source=1, destination=1)
            self.compare_with_numpy(torch_fn, np_fn, x, device=None, dtype=None)

            # Empty Sequence
            torch_fn = partial(fn, source=(), destination=())
            np_fn = partial(np.moveaxis, source=(), destination=())
            self.compare_with_numpy(torch_fn, np_fn, x, device=None, dtype=None)