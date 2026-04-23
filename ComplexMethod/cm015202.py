def test_scan_closure_RNN_partial_autograd(
        self, reverse, compile_mode, partial_grad, device
    ):
        dim = 1
        scan_fct = compile_mode_helper(scan, compile_mode)

        # The first two booleans are the xs
        # The second two are the inits
        # The last four are the additional_inputs
        autograds = []

        if partial_grad == "xs":
            # xs tests
            autograds.append([True, False, True, True, True, True, True, True])
            autograds.append([False, False, True, True, True, True, True, True])
        elif partial_grad == "init":
            # init tests
            autograds.append([True, True, False, True, True, True, True, True])
            autograds.append([True, True, False, False, True, True, True, True])
        elif partial_grad == "additional_inputs":
            # additional input tests
            autograds.append([True, True, True, True, False, True, False, True])
            autograds.append([True, True, True, True, False, False, False, False])
        elif partial_grad == "complex":
            # complex cases
            autograds.append([True, False, False, False, False, False, False, True])
            autograds.append([False, False, True, True, False, False, False, True])
        elif partial_grad == "random":
            # random tests
            import random

            for _ in range(5):
                autograds.append([bool(random.randint(0, 1)) for _ in range(8)])

        for autograd in autograds:
            x = torch.randn(3, 10, 5, device=device, requires_grad=autograd[0])
            x1 = torch.randn(3, 10, 5, device=device, requires_grad=autograd[1])
            h = torch.randn(3, 7, device=device, requires_grad=autograd[2])
            h_1 = torch.randn(3, 7, device=device, requires_grad=autograd[3])
            W_ih = torch.randn(5, 7, device=device, requires_grad=autograd[4])
            b_ih = torch.randn(7, device=device, requires_grad=autograd[5])
            W_hh = torch.randn(7, 7, device=device, requires_grad=autograd[6])
            b_hh = torch.randn(7, device=device, requires_grad=autograd[7])

            params = [
                p
                for p, a in zip([x, x1, h, h_1, W_ih, b_ih, W_hh, b_hh], autograd)
                if a
            ]

            def RNN(x: torch.Tensor, y: torch.Tensor):
                c_new_0 = x[0] + 1
                c_new_1 = x[1] + 1
                h_new = (
                    torch.tanh(c_new_1 + x[0] @ W_hh + b_hh)
                    + y[0] @ W_ih
                    + y[1] @ W_ih
                    + b_ih
                    + x[1]
                )
                return (c_new_0, c_new_1), h_new

            inits = (h, h_1)
            result = scan_fct(RNN, inits, (x, x1), dim=dim, reverse=reverse)
            result_exp = _fake_scan(RNN, (h, h_1), (x, x1), dim=dim, reverse=reverse)
            self.assertEqual(result, result_exp)

            if autograd:
                result_flat = pytree.tree_leaves(result)
                result_exp_flat = pytree.tree_leaves(result_exp)
                exp_grad_mask = [bool(r.requires_grad) for r in result_exp_flat]
                self.check_autograd(
                    [r for r, m in zip(result_flat, exp_grad_mask) if m],
                    [r for r, m in zip(result_exp_flat, exp_grad_mask) if m],
                    params,
                )