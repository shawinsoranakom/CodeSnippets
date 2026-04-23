def test_linear_autograd(self, device, bias, weight_layout):
        module = nn.Linear(4, 4, bias=bias, device=device)
        if weight_layout == torch.strided:
            pass
        elif weight_layout == torch.sparse_csr:
            module.weight = nn.Parameter(module.weight.to_sparse_csr())
        elif weight_layout == torch.sparse_csc:
            module.weight = nn.Parameter(module.weight.to_sparse_csc())
        elif weight_layout == torch.sparse_bsr:
            module.weight = nn.Parameter(module.weight.to_sparse_bsr((2, 2)))
        elif weight_layout == torch.sparse_bsc:
            module.weight = nn.Parameter(module.weight.to_sparse_bsc((2, 2)))
        elif weight_layout == torch.sparse_coo:
            module.weight = nn.Parameter(module.weight.to_sparse_coo())
        else:
            raise AssertionError

        inp = torch.randn(4, requires_grad=True, device=device)
        res = module(inp)
        if bias:
            expected = (torch.einsum("i,ji->j", inp, module.weight.to_dense())) + module.bias
        else:
            expected = (torch.einsum("i,ji->j", inp, module.weight.to_dense()))
        self.assertEqual(res, expected)

        grad_output = torch.randn(4, device=device)
        grads = torch.autograd.grad(res, [module.weight, inp], grad_output)
        grads_expected = torch.autograd.grad(expected, [module.weight, inp], grad_output)

        self.assertEqual(grads_expected[0].layout, weight_layout)

        for g, ge in zip(grads, grads_expected):
            self.assertEqual(g, ge)