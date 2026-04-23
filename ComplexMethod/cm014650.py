def test_advancedindex(self, device, dtype):
        # Tests for Integer Array Indexing, Part I - Purely integer array
        # indexing

        def consec(size, start=1):
            # Creates the sequence in float since CPU half doesn't support the
            # needed operations. Converts to dtype before returning.
            numel = reduce(operator.mul, size, 1)
            sequence = torch.ones(numel, dtype=torch.float, device=device).cumsum(0)
            sequence.add_(start - 1)
            return sequence.view(*size).to(dtype=dtype)

        # pick a random valid indexer type
        def ri(indices):
            choice = random.randint(0, 2)
            if choice == 0:
                return torch.LongTensor(indices).to(device)
            elif choice == 1:
                return list(indices)
            else:
                return tuple(indices)

        def validate_indexing(x):
            self.assertEqual(x[[0]], consec((1,)))
            self.assertEqual(x[ri([0]),], consec((1,)))
            self.assertEqual(x[ri([3]),], consec((1,), 4))
            self.assertEqual(x[[2, 3, 4]], consec((3,), 3))
            self.assertEqual(x[ri([2, 3, 4]),], consec((3,), 3))
            self.assertEqual(
                x[ri([0, 2, 4]),], torch.tensor([1, 3, 5], dtype=dtype, device=device)
            )

        def validate_setting(x):
            x[[0]] = -2
            self.assertEqual(x[[0]], torch.tensor([-2], dtype=dtype, device=device))
            x[[0]] = -1
            self.assertEqual(
                x[ri([0]),], torch.tensor([-1], dtype=dtype, device=device)
            )
            x[[2, 3, 4]] = 4
            self.assertEqual(
                x[[2, 3, 4]], torch.tensor([4, 4, 4], dtype=dtype, device=device)
            )
            x[ri([2, 3, 4]),] = 3
            self.assertEqual(
                x[ri([2, 3, 4]),], torch.tensor([3, 3, 3], dtype=dtype, device=device)
            )
            x[ri([0, 2, 4]),] = torch.tensor([5, 4, 3], dtype=dtype, device=device)
            self.assertEqual(
                x[ri([0, 2, 4]),], torch.tensor([5, 4, 3], dtype=dtype, device=device)
            )

        # Only validates indexing and setting for Halves
        if dtype == torch.half:
            reference = consec((10,))
            validate_indexing(reference)
            validate_setting(reference)
            return

        # Case 1: Purely Integer Array Indexing
        reference = consec((10,))
        validate_indexing(reference)

        # setting values
        validate_setting(reference)

        # Tensor with stride != 1
        # strided is [1, 3, 5, 7]
        reference = consec((10,))
        strided = torch.tensor((), dtype=dtype, device=device)
        strided.set_(
            reference.untyped_storage(),
            storage_offset=0,
            size=torch.Size([4]),
            stride=[2],
        )

        self.assertEqual(strided[[0]], torch.tensor([1], dtype=dtype, device=device))
        self.assertEqual(
            strided[ri([0]),], torch.tensor([1], dtype=dtype, device=device)
        )
        self.assertEqual(
            strided[ri([3]),], torch.tensor([7], dtype=dtype, device=device)
        )
        self.assertEqual(
            strided[[1, 2]], torch.tensor([3, 5], dtype=dtype, device=device)
        )
        self.assertEqual(
            strided[ri([1, 2]),], torch.tensor([3, 5], dtype=dtype, device=device)
        )
        self.assertEqual(
            strided[ri([[2, 1], [0, 3]]),],
            torch.tensor([[5, 3], [1, 7]], dtype=dtype, device=device),
        )

        # stride is [4, 8]
        strided = torch.tensor((), dtype=dtype, device=device)
        strided.set_(
            reference.untyped_storage(),
            storage_offset=4,
            size=torch.Size([2]),
            stride=[4],
        )
        self.assertEqual(strided[[0]], torch.tensor([5], dtype=dtype, device=device))
        self.assertEqual(
            strided[ri([0]),], torch.tensor([5], dtype=dtype, device=device)
        )
        self.assertEqual(
            strided[ri([1]),], torch.tensor([9], dtype=dtype, device=device)
        )
        self.assertEqual(
            strided[[0, 1]], torch.tensor([5, 9], dtype=dtype, device=device)
        )
        self.assertEqual(
            strided[ri([0, 1]),], torch.tensor([5, 9], dtype=dtype, device=device)
        )
        self.assertEqual(
            strided[ri([[0, 1], [1, 0]]),],
            torch.tensor([[5, 9], [9, 5]], dtype=dtype, device=device),
        )

        # reference is 1 2
        #              3 4
        #              5 6
        reference = consec((3, 2))
        self.assertEqual(
            reference[ri([0, 1, 2]), ri([0])],
            torch.tensor([1, 3, 5], dtype=dtype, device=device),
        )
        self.assertEqual(
            reference[ri([0, 1, 2]), ri([1])],
            torch.tensor([2, 4, 6], dtype=dtype, device=device),
        )
        self.assertEqual(reference[ri([0]), ri([0])], consec((1,)))
        self.assertEqual(reference[ri([2]), ri([1])], consec((1,), 6))
        self.assertEqual(
            reference[(ri([0, 0]), ri([0, 1]))],
            torch.tensor([1, 2], dtype=dtype, device=device),
        )
        self.assertEqual(
            reference[(ri([0, 1, 1, 0, 2]), ri([1]))],
            torch.tensor([2, 4, 4, 2, 6], dtype=dtype, device=device),
        )
        self.assertEqual(
            reference[(ri([0, 0, 1, 1]), ri([0, 1, 0, 0]))],
            torch.tensor([1, 2, 3, 3], dtype=dtype, device=device),
        )

        rows = ri([[0, 0], [1, 2]])
        columns = ([0],)
        self.assertEqual(
            reference[rows, columns],
            torch.tensor([[1, 1], [3, 5]], dtype=dtype, device=device),
        )

        rows = ri([[0, 0], [1, 2]])
        columns = ri([1, 0])
        self.assertEqual(
            reference[rows, columns],
            torch.tensor([[2, 1], [4, 5]], dtype=dtype, device=device),
        )
        rows = ri([[0, 0], [1, 2]])
        columns = ri([[0, 1], [1, 0]])
        self.assertEqual(
            reference[rows, columns],
            torch.tensor([[1, 2], [4, 5]], dtype=dtype, device=device),
        )

        # setting values
        reference[ri([0]), ri([1])] = -1
        self.assertEqual(
            reference[ri([0]), ri([1])], torch.tensor([-1], dtype=dtype, device=device)
        )
        reference[ri([0, 1, 2]), ri([0])] = torch.tensor(
            [-1, 2, -4], dtype=dtype, device=device
        )
        self.assertEqual(
            reference[ri([0, 1, 2]), ri([0])],
            torch.tensor([-1, 2, -4], dtype=dtype, device=device),
        )
        reference[rows, columns] = torch.tensor(
            [[4, 6], [2, 3]], dtype=dtype, device=device
        )
        self.assertEqual(
            reference[rows, columns],
            torch.tensor([[4, 6], [2, 3]], dtype=dtype, device=device),
        )

        # Verify still works with Transposed (i.e. non-contiguous) Tensors

        reference = torch.tensor(
            [[0, 1, 2, 3], [4, 5, 6, 7], [8, 9, 10, 11]], dtype=dtype, device=device
        ).t_()

        # Transposed: [[0, 4, 8],
        #              [1, 5, 9],
        #              [2, 6, 10],
        #              [3, 7, 11]]

        self.assertEqual(
            reference[ri([0, 1, 2]), ri([0])],
            torch.tensor([0, 1, 2], dtype=dtype, device=device),
        )
        self.assertEqual(
            reference[ri([0, 1, 2]), ri([1])],
            torch.tensor([4, 5, 6], dtype=dtype, device=device),
        )
        self.assertEqual(
            reference[ri([0]), ri([0])], torch.tensor([0], dtype=dtype, device=device)
        )
        self.assertEqual(
            reference[ri([2]), ri([1])], torch.tensor([6], dtype=dtype, device=device)
        )
        self.assertEqual(
            reference[(ri([0, 0]), ri([0, 1]))],
            torch.tensor([0, 4], dtype=dtype, device=device),
        )
        self.assertEqual(
            reference[(ri([0, 1, 1, 0, 3]), ri([1]))],
            torch.tensor([4, 5, 5, 4, 7], dtype=dtype, device=device),
        )
        self.assertEqual(
            reference[(ri([0, 0, 1, 1]), ri([0, 1, 0, 0]))],
            torch.tensor([0, 4, 1, 1], dtype=dtype, device=device),
        )

        rows = ri([[0, 0], [1, 2]])
        columns = ([0],)
        self.assertEqual(
            reference[rows, columns],
            torch.tensor([[0, 0], [1, 2]], dtype=dtype, device=device),
        )

        rows = ri([[0, 0], [1, 2]])
        columns = ri([1, 0])
        self.assertEqual(
            reference[rows, columns],
            torch.tensor([[4, 0], [5, 2]], dtype=dtype, device=device),
        )
        rows = ri([[0, 0], [1, 3]])
        columns = ri([[0, 1], [1, 2]])
        self.assertEqual(
            reference[rows, columns],
            torch.tensor([[0, 4], [5, 11]], dtype=dtype, device=device),
        )

        # setting values
        reference[ri([0]), ri([1])] = -1
        self.assertEqual(
            reference[ri([0]), ri([1])], torch.tensor([-1], dtype=dtype, device=device)
        )
        reference[ri([0, 1, 2]), ri([0])] = torch.tensor(
            [-1, 2, -4], dtype=dtype, device=device
        )
        self.assertEqual(
            reference[ri([0, 1, 2]), ri([0])],
            torch.tensor([-1, 2, -4], dtype=dtype, device=device),
        )
        reference[rows, columns] = torch.tensor(
            [[4, 6], [2, 3]], dtype=dtype, device=device
        )
        self.assertEqual(
            reference[rows, columns],
            torch.tensor([[4, 6], [2, 3]], dtype=dtype, device=device),
        )

        # stride != 1

        # strided is [[1 3 5 7],
        #             [9 11 13 15]]

        reference = torch.arange(0.0, 24, dtype=dtype, device=device).view(3, 8)
        strided = torch.tensor((), dtype=dtype, device=device)
        strided.set_(
            reference.untyped_storage(), 1, size=torch.Size([2, 4]), stride=[8, 2]
        )

        self.assertEqual(
            strided[ri([0, 1]), ri([0])],
            torch.tensor([1, 9], dtype=dtype, device=device),
        )
        self.assertEqual(
            strided[ri([0, 1]), ri([1])],
            torch.tensor([3, 11], dtype=dtype, device=device),
        )
        self.assertEqual(
            strided[ri([0]), ri([0])], torch.tensor([1], dtype=dtype, device=device)
        )
        self.assertEqual(
            strided[ri([1]), ri([3])], torch.tensor([15], dtype=dtype, device=device)
        )
        self.assertEqual(
            strided[(ri([0, 0]), ri([0, 3]))],
            torch.tensor([1, 7], dtype=dtype, device=device),
        )
        self.assertEqual(
            strided[(ri([1]), ri([0, 1, 1, 0, 3]))],
            torch.tensor([9, 11, 11, 9, 15], dtype=dtype, device=device),
        )
        self.assertEqual(
            strided[(ri([0, 0, 1, 1]), ri([0, 1, 0, 0]))],
            torch.tensor([1, 3, 9, 9], dtype=dtype, device=device),
        )

        rows = ri([[0, 0], [1, 1]])
        columns = ([0],)
        self.assertEqual(
            strided[rows, columns],
            torch.tensor([[1, 1], [9, 9]], dtype=dtype, device=device),
        )

        rows = ri([[0, 1], [1, 0]])
        columns = ri([1, 2])
        self.assertEqual(
            strided[rows, columns],
            torch.tensor([[3, 13], [11, 5]], dtype=dtype, device=device),
        )
        rows = ri([[0, 0], [1, 1]])
        columns = ri([[0, 1], [1, 2]])
        self.assertEqual(
            strided[rows, columns],
            torch.tensor([[1, 3], [11, 13]], dtype=dtype, device=device),
        )

        # setting values

        # strided is [[10, 11],
        #             [17, 18]]

        reference = torch.arange(0.0, 24, dtype=dtype, device=device).view(3, 8)
        strided = torch.tensor((), dtype=dtype, device=device)
        strided.set_(
            reference.untyped_storage(), 10, size=torch.Size([2, 2]), stride=[7, 1]
        )
        self.assertEqual(
            strided[ri([0]), ri([1])], torch.tensor([11], dtype=dtype, device=device)
        )
        strided[ri([0]), ri([1])] = -1
        self.assertEqual(
            strided[ri([0]), ri([1])], torch.tensor([-1], dtype=dtype, device=device)
        )

        reference = torch.arange(0.0, 24, dtype=dtype, device=device).view(3, 8)
        strided = torch.tensor((), dtype=dtype, device=device)
        strided.set_(
            reference.untyped_storage(), 10, size=torch.Size([2, 2]), stride=[7, 1]
        )
        self.assertEqual(
            strided[ri([0, 1]), ri([1, 0])],
            torch.tensor([11, 17], dtype=dtype, device=device),
        )
        strided[ri([0, 1]), ri([1, 0])] = torch.tensor(
            [-1, 2], dtype=dtype, device=device
        )
        self.assertEqual(
            strided[ri([0, 1]), ri([1, 0])],
            torch.tensor([-1, 2], dtype=dtype, device=device),
        )

        reference = torch.arange(0.0, 24, dtype=dtype, device=device).view(3, 8)
        strided = torch.tensor((), dtype=dtype, device=device)
        strided.set_(
            reference.untyped_storage(), 10, size=torch.Size([2, 2]), stride=[7, 1]
        )

        rows = ri([[0], [1]])
        columns = ri([[0, 1], [0, 1]])
        self.assertEqual(
            strided[rows, columns],
            torch.tensor([[10, 11], [17, 18]], dtype=dtype, device=device),
        )
        strided[rows, columns] = torch.tensor(
            [[4, 6], [2, 3]], dtype=dtype, device=device
        )
        self.assertEqual(
            strided[rows, columns],
            torch.tensor([[4, 6], [2, 3]], dtype=dtype, device=device),
        )

        # Tests using less than the number of dims, and ellipsis

        # reference is 1 2
        #              3 4
        #              5 6
        reference = consec((3, 2))
        self.assertEqual(
            reference[ri([0, 2]),],
            torch.tensor([[1, 2], [5, 6]], dtype=dtype, device=device),
        )
        self.assertEqual(
            reference[ri([1]), ...], torch.tensor([[3, 4]], dtype=dtype, device=device)
        )
        self.assertEqual(
            reference[..., ri([1])],
            torch.tensor([[2], [4], [6]], dtype=dtype, device=device),
        )

        # verify too many indices fails
        with self.assertRaises(IndexError):
            reference[ri([1]), ri([0, 2]), ri([3])]

        # test invalid index fails
        reference = torch.empty(10, dtype=dtype, device=device)
        # can't test cuda/xpu because it is a device assert
        if reference.device.type == "cpu":
            for err_idx in (10, -11):
                with self.assertRaisesRegex(IndexError, r"out of"):
                    reference[err_idx]
                with self.assertRaisesRegex(IndexError, r"out of"):
                    reference[torch.LongTensor([err_idx]).to(device)]
                with self.assertRaisesRegex(IndexError, r"out of"):
                    reference[[err_idx]]

        def tensor_indices_to_np(tensor, indices):
            # convert the Torch Tensor to a numpy array
            tensor = tensor.to(device="cpu")
            npt = tensor.numpy()

            # convert indices
            idxs = tuple(
                i.tolist() if isinstance(i, torch.LongTensor) else i for i in indices
            )

            return npt, idxs

        def get_numpy(tensor, indices):
            npt, idxs = tensor_indices_to_np(tensor, indices)

            # index and return as a Torch Tensor
            return torch.tensor(npt[idxs], dtype=dtype, device=device)

        def set_numpy(tensor, indices, value):
            if not isinstance(value, int):
                if self.device_type != "cpu":
                    value = value.cpu()
                value = value.numpy()

            npt, idxs = tensor_indices_to_np(tensor, indices)
            npt[idxs] = value
            return npt

        def assert_get_eq(tensor, indexer):
            self.assertEqual(tensor[indexer], get_numpy(tensor, indexer))

        def assert_set_eq(tensor, indexer, val):
            pyt = tensor.clone()
            numt = tensor.clone()
            pyt[indexer] = val
            numt = torch.tensor(
                set_numpy(numt, indexer, val), dtype=dtype, device=device
            )
            self.assertEqual(pyt, numt)

        def assert_backward_eq(tensor, indexer):
            cpu = tensor.float().detach().clone().requires_grad_(True)
            outcpu = cpu[indexer]
            gOcpu = torch.rand_like(outcpu)
            outcpu.backward(gOcpu)
            dev = cpu.to(device).detach().requires_grad_(True)
            outdev = dev[indexer]
            outdev.backward(gOcpu.to(device))
            self.assertEqual(cpu.grad, dev.grad)

        def get_set_tensor(indexed, indexer):
            set_size = indexed[indexer].size()
            set_count = indexed[indexer].numel()
            set_tensor = torch.randperm(set_count).view(set_size).double().to(device)
            return set_tensor

        # Tensor is  0  1  2  3  4
        #            5  6  7  8  9
        #           10 11 12 13 14
        #           15 16 17 18 19
        reference = torch.arange(0.0, 20, dtype=dtype, device=device).view(4, 5)

        indices_to_test = [
            # grab the second, fourth columns
            (slice(None), [1, 3]),
            # first, third rows,
            ([0, 2], slice(None)),
            # weird shape
            (slice(None), [[0, 1], [2, 3]]),
            # negatives
            ([-1], [0]),
            ([0, 2], [-1]),
            (slice(None), [-1]),
        ]

        # only test dupes on gets
        get_indices_to_test = indices_to_test + [(slice(None), [0, 1, 1, 2, 2])]

        for indexer in get_indices_to_test:
            assert_get_eq(reference, indexer)
            if self.device_type != "cpu":
                assert_backward_eq(reference, indexer)

        for indexer in indices_to_test:
            assert_set_eq(reference, indexer, 44)
            assert_set_eq(reference, indexer, get_set_tensor(reference, indexer))

        reference = torch.arange(0.0, 160, dtype=dtype, device=device).view(4, 8, 5)

        indices_to_test = [
            (slice(None), slice(None), (0, 3, 4)),
            (slice(None), (2, 4, 5, 7), slice(None)),
            ((2, 3), slice(None), slice(None)),
            (slice(None), (0, 2, 3), (1, 3, 4)),
            (slice(None), (0,), (1, 2, 4)),
            (slice(None), (0, 1, 3), (4,)),
            (slice(None), ((0, 1), (1, 0)), ((2, 3),)),
            (slice(None), ((0, 1), (2, 3)), ((0,),)),
            (slice(None), ((5, 6),), ((0, 3), (4, 4))),
            ((0, 2, 3), (1, 3, 4), slice(None)),
            ((0,), (1, 2, 4), slice(None)),
            ((0, 1, 3), (4,), slice(None)),
            (((0, 1), (1, 0)), ((2, 1), (3, 5)), slice(None)),
            (((0, 1), (1, 0)), ((2, 3),), slice(None)),
            (((0, 1), (2, 3)), ((0,),), slice(None)),
            (((2, 1),), ((0, 3), (4, 4)), slice(None)),
            (((2,),), ((0, 3), (4, 1)), slice(None)),
            # non-contiguous indexing subspace
            ((0, 2, 3), slice(None), (1, 3, 4)),
            # [...]
            # less dim, ellipsis
            ((0, 2),),
            ((0, 2), slice(None)),
            ((0, 2), Ellipsis),
            ((0, 2), slice(None), Ellipsis),
            ((0, 2), Ellipsis, slice(None)),
            ((0, 2), (1, 3)),
            ((0, 2), (1, 3), Ellipsis),
            (Ellipsis, (1, 3), (2, 3)),
            (Ellipsis, (2, 3, 4)),
            (Ellipsis, slice(None), (2, 3, 4)),
            (slice(None), Ellipsis, (2, 3, 4)),
            # ellipsis counts for nothing
            (Ellipsis, slice(None), slice(None), (0, 3, 4)),
            (slice(None), Ellipsis, slice(None), (0, 3, 4)),
            (slice(None), slice(None), Ellipsis, (0, 3, 4)),
            (slice(None), slice(None), (0, 3, 4), Ellipsis),
            (Ellipsis, ((0, 1), (1, 0)), ((2, 1), (3, 5)), slice(None)),
            (((0, 1), (1, 0)), ((2, 1), (3, 5)), Ellipsis, slice(None)),
            (((0, 1), (1, 0)), ((2, 1), (3, 5)), slice(None), Ellipsis),
        ]

        for indexer in indices_to_test:
            assert_get_eq(reference, indexer)
            assert_set_eq(reference, indexer, 212)
            assert_set_eq(reference, indexer, get_set_tensor(reference, indexer))
            if torch.accelerator.is_available():
                assert_backward_eq(reference, indexer)

        reference = torch.arange(0.0, 1296, dtype=dtype, device=device).view(3, 9, 8, 6)

        indices_to_test = [
            (slice(None), slice(None), slice(None), (0, 3, 4)),
            (slice(None), slice(None), (2, 4, 5, 7), slice(None)),
            (slice(None), (2, 3), slice(None), slice(None)),
            ((1, 2), slice(None), slice(None), slice(None)),
            (slice(None), slice(None), (0, 2, 3), (1, 3, 4)),
            (slice(None), slice(None), (0,), (1, 2, 4)),
            (slice(None), slice(None), (0, 1, 3), (4,)),
            (slice(None), slice(None), ((0, 1), (1, 0)), ((2, 3),)),
            (slice(None), slice(None), ((0, 1), (2, 3)), ((0,),)),
            (slice(None), slice(None), ((5, 6),), ((0, 3), (4, 4))),
            (slice(None), (0, 2, 3), (1, 3, 4), slice(None)),
            (slice(None), (0,), (1, 2, 4), slice(None)),
            (slice(None), (0, 1, 3), (4,), slice(None)),
            (slice(None), ((0, 1), (3, 4)), ((2, 3), (0, 1)), slice(None)),
            (slice(None), ((0, 1), (3, 4)), ((2, 3),), slice(None)),
            (slice(None), ((0, 1), (3, 2)), ((0,),), slice(None)),
            (slice(None), ((2, 1),), ((0, 3), (6, 4)), slice(None)),
            (slice(None), ((2,),), ((0, 3), (4, 2)), slice(None)),
            ((0, 1, 2), (1, 3, 4), slice(None), slice(None)),
            ((0,), (1, 2, 4), slice(None), slice(None)),
            ((0, 1, 2), (4,), slice(None), slice(None)),
            (((0, 1), (0, 2)), ((2, 4), (1, 5)), slice(None), slice(None)),
            (((0, 1), (1, 2)), ((2, 0),), slice(None), slice(None)),
            (((2, 2),), ((0, 3), (4, 5)), slice(None), slice(None)),
            (((2,),), ((0, 3), (4, 5)), slice(None), slice(None)),
            (slice(None), (3, 4, 6), (0, 2, 3), (1, 3, 4)),
            (slice(None), (2, 3, 4), (1, 3, 4), (4,)),
            (slice(None), (0, 1, 3), (4,), (1, 3, 4)),
            (slice(None), (6,), (0, 2, 3), (1, 3, 4)),
            (slice(None), (2, 3, 5), (3,), (4,)),
            (slice(None), (0,), (4,), (1, 3, 4)),
            (slice(None), (6,), (0, 2, 3), (1,)),
            (slice(None), ((0, 3), (3, 6)), ((0, 1), (1, 3)), ((5, 3), (1, 2))),
            ((2, 2, 1), (0, 2, 3), (1, 3, 4), slice(None)),
            ((2, 0, 1), (1, 2, 3), (4,), slice(None)),
            ((0, 1, 2), (4,), (1, 3, 4), slice(None)),
            ((0,), (0, 2, 3), (1, 3, 4), slice(None)),
            ((0, 2, 1), (3,), (4,), slice(None)),
            ((0,), (4,), (1, 3, 4), slice(None)),
            ((1,), (0, 2, 3), (1,), slice(None)),
            (((1, 2), (1, 2)), ((0, 1), (2, 3)), ((2, 3), (3, 5)), slice(None)),
            # less dim, ellipsis
            (Ellipsis, (0, 3, 4)),
            (Ellipsis, slice(None), (0, 3, 4)),
            (Ellipsis, slice(None), slice(None), (0, 3, 4)),
            (slice(None), Ellipsis, (0, 3, 4)),
            (slice(None), slice(None), Ellipsis, (0, 3, 4)),
            (slice(None), (0, 2, 3), (1, 3, 4)),
            (slice(None), (0, 2, 3), (1, 3, 4), Ellipsis),
            (Ellipsis, (0, 2, 3), (1, 3, 4), slice(None)),
            ((0,), (1, 2, 4)),
            ((0,), (1, 2, 4), slice(None)),
            ((0,), (1, 2, 4), Ellipsis),
            ((0,), (1, 2, 4), Ellipsis, slice(None)),
            ((1,),),
            ((0, 2, 1), (3,), (4,)),
            ((0, 2, 1), (3,), (4,), slice(None)),
            ((0, 2, 1), (3,), (4,), Ellipsis),
            (Ellipsis, (0, 2, 1), (3,), (4,)),
        ]

        for indexer in indices_to_test:
            assert_get_eq(reference, indexer)
            assert_set_eq(reference, indexer, 1333)
            assert_set_eq(reference, indexer, get_set_tensor(reference, indexer))
        indices_to_test += [
            (slice(None), slice(None), [[0, 1], [1, 0]], [[2, 3], [3, 0]]),
            (slice(None), slice(None), [[2]], [[0, 3], [4, 4]]),
        ]
        for indexer in indices_to_test:
            assert_get_eq(reference, indexer)
            assert_set_eq(reference, indexer, 1333)
            if self.device_type != "cpu":
                assert_backward_eq(reference, indexer)