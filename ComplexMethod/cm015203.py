def _check_autograd(self, result, result_exp, autograd_param):
        grad_param = [p for p in autograd_param if p.requires_grad]

        result_flatten, _ = pytree.tree_flatten(result)
        result_exp_flatten, _ = pytree.tree_flatten(result_exp)
        result_flatten = [r for r in result_flatten if r.requires_grad]
        result_exp_flatten = [r for r in result_exp_flatten if r.requires_grad]

        # Check the result and parameter lists
        if len(result_flatten) != len(result_exp_flatten):
            raise AssertionError(
                "The number of elements requiring gradients is different for the results and the expected results"
            )

        grad_exp_init = [torch.ones_like(el) for el in result_exp_flatten]
        expected_grads = torch.autograd.grad(
            result_exp_flatten, grad_param, grad_exp_init
        )
        grad_init = [torch.ones_like(el) for el in result_flatten]
        grads = torch.autograd.grad(result_flatten, grad_param, grad_init)

        self.assertEqual(grads, expected_grads, atol=6e-05, rtol=6e-06)