def _run_test(self, model, model_fake, inputs, autograd_param=None):
        result = model(inputs)
        result_exp = model_fake(inputs)
        self.assertEqual(result, result_exp)

        if autograd_param is not None and any(
            par.requires_grad for par in autograd_param
        ):
            result_flat = pytree.tree_leaves(result)
            result_exp_flat = pytree.tree_leaves(result_exp)
            exp_grad_mask = [bool(r.requires_grad) for r in result_exp_flat]

            self._check_autograd(
                [r for r, m in zip(result_flat, exp_grad_mask) if m],
                [r for r, m in zip(result_exp_flat, exp_grad_mask) if m],
                autograd_param,
            )

        # Return the result of the functions under test for further investigations
        return result