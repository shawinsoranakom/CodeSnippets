def test_empty_like(self, device, dtype):
        ntensors = 4
        nt = random_nt(device, dtype, ntensors, (4, 4))

        # Create empty on same device as original nested tensor
        nt_empty = torch.empty_like(nt)
        if not nt.is_same_size(nt_empty):
            raise AssertionError("Expected nt and nt_empty to have the same size")
        self.assertEqual(nt.dtype, nt_empty.dtype)
        self.assertEqual(nt.device, nt_empty.device)
        self.assertEqual(nt.layout, nt_empty.layout)

        if torch.cuda.is_available():
            if device == "cpu":
                nt_cuda = torch.empty_like(nt, device="cuda")
                self.assertEqual(torch.device("cuda").type, nt_cuda.device.type)
            else:
                nt_cpu = torch.empty_like(nt, device="cpu")
                self.assertEqual(torch.device("cpu").type, nt_cpu.device.type)

        # Check changing dtype of empty_like nested tensor output
        dtype_set = {torch.float, torch.float16, torch.double}
        for other_dtype in dtype_set - {dtype}:
            nt_empty_other_dtype = torch.empty_like(nt, dtype=other_dtype)
            self.assertEqual(nt.dtype, dtype)
            self.assertEqual(nt_empty_other_dtype.dtype, other_dtype)
            self.assertEqual(nt.device, nt_empty.device)
            self.assertEqual(nt.layout, nt_empty.layout)

        # Create tensor for autograd
        nt_empty_req_grad = torch.empty_like(nt, requires_grad=True)
        self.assertEqual(nt_empty_req_grad.requires_grad, True)

        # Test noncontiguous tensor does not fail to copy
        nt_cont, nt_noncont = random_nt_noncontiguous_pair((2, 3, 6, 7))
        nt_empty = torch.empty_like(nt_cont)
        if not nt_cont.is_same_size(nt_empty):
            raise AssertionError("Expected nt_cont and nt_empty to have the same size")
        nt_empty_non_contig = torch.empty_like(nt_noncont)
        if not nt_noncont.is_same_size(nt_empty_non_contig):
            raise AssertionError(
                "Expected nt_noncont and nt_empty_non_contig to have the same size"
            )

        # Test the contiguous memory format option
        nt_empty_contig = torch.empty_like(
            nt_cont, memory_format=torch.contiguous_format
        )
        if not nt_cont.is_same_size(nt_empty_contig):
            raise AssertionError(
                "Expected nt_cont and nt_empty_contig to have the same size"
            )
        if not nt_empty_contig.is_contiguous():
            raise AssertionError("Expected nt_empty_contig to be contiguous")

        nt_empty_non_contig = torch.empty_like(
            nt_noncont, memory_format=torch.contiguous_format
        )
        if not nt_noncont.is_same_size(nt_empty_non_contig):
            raise AssertionError(
                "Expected nt_noncont and nt_empty_non_contig to have the same size"
            )
        if not nt_empty_non_contig.is_contiguous():
            raise AssertionError("Expected nt_empty_non_contig to be contiguous")

        # Test other memory formats fail
        self.assertRaises(
            RuntimeError,
            lambda: torch.empty_like(nt_cont, memory_format=torch.channels_last),
        )
        self.assertRaises(
            RuntimeError,
            lambda: torch.empty_like(nt_noncont, memory_format=torch.channels_last),
        )
        self.assertRaises(
            RuntimeError,
            lambda: torch.empty_like(nt_cont, memory_format=torch.channels_last_3d),
        )
        self.assertRaises(
            RuntimeError,
            lambda: torch.empty_like(nt_noncont, memory_format=torch.channels_last_3d),
        )