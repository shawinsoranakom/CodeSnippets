def test_sparse_mm_backward(self):
        size = (3, 3)

        mm_test_cases = product(*(([False, True],) * 4))

        for a_req_grad, a_is_sparse, b_req_grad, b_is_sparse in mm_test_cases:
            # We should only be testing cases with sparse inputs, and at least one
            # input needs to require grad so we can call a backward pass
            if not ((a_is_sparse or b_is_sparse) and (a_req_grad or b_req_grad)):
                continue
            a = torch.randn(size)
            if a_is_sparse:
                # detaching as `a` needs to be a leaf
                a = a.to_sparse().detach()
            b = torch.randn(size)
            if b_is_sparse:
                # detaching as `b` needs to be a leaf
                b = b.to_sparse().detach()

            a = a.requires_grad_(a_req_grad)
            b = b.requires_grad_(b_req_grad)

            r = a.mm(b)
            s = r.sum().backward()
            a_grad = None if a.grad is None else a.grad.detach().clone()
            b_grad = None if b.grad is None else b.grad.detach().clone()

            # Redo with only dense tensors
            a = (
                (a.to_dense() if a.is_sparse else a)
                .clone()
                .detach()
                .requires_grad_(a_req_grad)
            )
            b = (
                (b.to_dense() if b.is_sparse else b)
                .clone()
                .detach()
                .requires_grad_(b_req_grad)
            )

            r = a.mm(b)
            r.sum().backward()

            self.assertEqual(a_grad, a.grad)
            self.assertEqual(b_grad, b.grad)