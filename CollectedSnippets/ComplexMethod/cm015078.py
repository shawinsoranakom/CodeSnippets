def test_binary_op_list_error_cases(self, device, dtype, op):
        foreach_op, foreach_op_, ref, ref_ = (
            op.method_variant,
            op.inplace_variant,
            op.ref,
            op.ref_inplace,
        )
        tensors1 = []
        tensors2 = []
        ops_to_test = [foreach_op, foreach_op_]

        # Empty lists
        for fop in ops_to_test:
            with self.assertRaisesRegex(
                RuntimeError, "Tensor list must have at least one tensor."
            ):
                fop(tensors1, tensors2)

        # One empty list
        tensors1.append(torch.tensor([1], device=device, dtype=dtype))
        for fop in ops_to_test:
            with self.assertRaisesRegex(
                RuntimeError,
                "Tensor list must have same number of elements as scalar list.",
            ):
                fop(tensors1, tensors2)

        # Lists have different amount of tensors
        tensors2.append(torch.tensor([1], device=device))
        tensors2.append(torch.tensor([1], device=device))
        for fop in ops_to_test:
            with self.assertRaisesRegex(
                RuntimeError,
                "Tensor lists must have the same number of tensors, got 1 and 2",
            ):
                fop(tensors1, tensors2)
            with self.assertRaisesRegex(
                RuntimeError,
                "Tensor lists must have the same number of tensors, got 2 and 1",
            ):
                fop(tensors2, tensors1)

        # Corresponding tensors with different sizes that aren't compatible with broadcast
        # If sizes are different then foreach chooses slow path, thus error messages are expected
        # to be the same as torch regular function.
        tensors1 = [torch.zeros(10, 10, device=device, dtype=dtype) for _ in range(10)]
        tensors2 = [torch.ones(11, 11, device=device, dtype=dtype) for _ in range(10)]

        if dtype == torch.bool and foreach_op == torch._foreach_sub:
            for fop in ops_to_test:
                with self.assertRaisesRegex(RuntimeError, re.escape(_BOOL_SUB_ERR_MSG)):
                    fop(tensors1, tensors2)
            return
        with self.assertRaisesRegex(
            RuntimeError,
            r"The size of tensor a \(10\) must match the size of tensor b \(11\) at non-singleton dimension 1",
        ):
            foreach_op(tensors1, tensors2)
        with self.assertRaisesRegex(
            RuntimeError,
            r"The size of tensor a \(10\) must match the size of tensor b \(11\) at non-singleton dimension 1",
        ):
            foreach_op_(tensors1, tensors2)

        # different devices
        if self.device_type == "cuda" and torch.cuda.device_count() > 1:
            tensor1 = torch.zeros(10, 10, device="cuda:0", dtype=dtype)
            tensor2 = torch.ones(10, 10, device="cuda:1", dtype=dtype)
            with self.assertRaisesRegex(
                RuntimeError, "Expected all tensors to be on the same device"
            ):
                foreach_op([tensor1], [tensor2])
            if (
                dtype in integral_types_and(torch.bool)
                and foreach_op == torch._foreach_div
            ):
                with self.assertRaisesRegex(RuntimeError, "result type"):
                    foreach_op_([tensor1], [tensor2])
            else:
                with self.assertRaisesRegex(
                    RuntimeError, "Expected all tensors to be on the same device"
                ):
                    foreach_op_([tensor1], [tensor2])