def test(n=10,                       # how many tests to generate
                 n_labels=5,                 # how many labels available
                 min_ops=1, max_ops=4,       # min and max number of operands per test
                 min_dims=1, max_dims=3,     # min and max number of dimensions per operand
                 min_size=1, max_size=8,     # min and max size of each dimension
                 max_out_dim=3,              # max number of dimensions for the output
                 enable_diagonals=True,      # controls if labels can be repeated for diagonals
                 ellipsis_prob=0.5,          # probability of including ellipsis in operand
                 broadcasting_prob=0.1):     # probability of turning some dim sizes 1 for broadcasting

            all_labels = torch.arange(52)

            if not (0 <= n):
                raise AssertionError(f"n should be >= 0, got {n}")
            if not (0 <= n_labels < len(all_labels)):
                raise AssertionError(f"n_labels should be in [0, {len(all_labels)}), got {n_labels}")
            if not (0 < min_ops <= max_ops):
                raise AssertionError(f"invalid min_ops={min_ops}, max_ops={max_ops}")
            if not (0 <= min_dims <= max_dims):
                raise AssertionError(f"invalid min_dims={min_dims}, max_dims={max_dims}")
            if not (0 <= min_size <= max_size):
                raise AssertionError(f"invalid min_size={min_size}, max_size={max_size}")
            if not (0 <= max_out_dim):
                raise AssertionError(f"max_out_dim should be >= 0, got {max_out_dim}")
            if not (enable_diagonals or max_dims <= n_labels):
                raise AssertionError(f"enable_diagonals is False but max_dims={max_dims} > n_labels={n_labels}")

            for _ in range(n):

                # Select a subset of labels for this test and give them random sizes
                possible_labels = all_labels[torch.randperm(len(all_labels))[:n_labels]]
                labels_size = torch.randint_like(all_labels, min_size, max_size + 1)
                ellipsis_shape = torch.randint(min_size, max_size + 1, (max_dims - min_dims,))

                operands = []
                sublists = []

                ell_size = 0
                valid_labels = set()

                # create random input operands
                for _ in range(random.randint(min_ops, max_ops)):
                    n_dim = random.randint(min_dims, max_dims)
                    labels_idx = torch.ones(len(possible_labels)).multinomial(n_dim, enable_diagonals)
                    labels = possible_labels[labels_idx]
                    valid_labels.update(labels.tolist())
                    shape = labels_size[labels]

                    # turn some dimensions to size 1 for testing broadcasting
                    mask = Binomial(probs=broadcasting_prob).sample((n_dim,))
                    broadcast_labels = torch.unique(labels[mask == 1])
                    shape[(labels[..., None] == broadcast_labels).any(-1)] = 1

                    labels = labels.tolist()
                    shape = shape.tolist()

                    # include ellipsis if not all dimensions were assigned a label already
                    if n_dim < max_dims and torch.rand(1) < ellipsis_prob:
                        ell_num_dim = random.randint(1, max_dims - n_dim)
                        ell_size = max(ell_size, ell_num_dim)
                        ell_shape = ellipsis_shape[-ell_num_dim:]
                        # again, turn some dimensions to size 1 for broadcasting
                        mask = Binomial(probs=broadcasting_prob).sample((ell_num_dim,))
                        ell_shape[mask == 1] = 1
                        ell_index = random.randint(0, n_dim)
                        shape[ell_index:ell_index] = ell_shape
                        labels.insert(ell_index, ...)

                    operands.append(make_tensor(shape, dtype=dtype, device=device))
                    sublists.append(labels)

                # NumPy has a bug with the sublist format so for now we compare PyTorch sublist
                # implementation against the equation format implementation of NumPy
                # see https://github.com/numpy/numpy/issues/10926
                np_operands = [op.cpu().numpy() for op in operands]

                # test equation format
                equation = ','.join(convert_sublist(l) for l in sublists)
                self._check_einsum(equation, *operands, np_args=(equation, *np_operands))

                # test sublist format
                args = list(itertools.chain.from_iterable(zip(operands, sublists)))
                self._check_einsum(*args, np_args=(equation, *np_operands))

                # generate an explicit output
                out_sublist = []
                num_out_labels = max(0, random.randint(0, min(max_out_dim, len(valid_labels))) - ell_size)
                if num_out_labels > 0:
                    out_labels_idx = torch.ones(len(valid_labels)).multinomial(num_out_labels)
                    out_sublist = torch.tensor(list(valid_labels))[out_labels_idx].tolist()
                out_sublist.insert(random.randint(0, num_out_labels), ...)

                # test equation format with explicit output
                equation += '->' + convert_sublist(out_sublist)
                self._check_einsum(equation, *operands, np_args=(equation, *np_operands))

                # test sublist format with explicit output
                args.append(out_sublist)
                self._check_einsum(*args, np_args=(equation, *np_operands))