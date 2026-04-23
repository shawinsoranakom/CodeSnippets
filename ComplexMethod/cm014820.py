def _do_test_multi_input(self, module, input):
        class TestModule(nn.Module):
            def __init__(self, module):
                super().__init__()
                self.module = module

            def forward(self, input):
                return self.module(input) + self.module(input)

        batch_size = input.shape[0]
        diff_input = input.dtype == torch.float or input.dtype == torch.double
        if diff_input:
            input.requires_grad_()
        with freeze_rng_state():
            # get per sample grads with ExpandedWeights context manager, calling .backward() twice
            test_module = TestModule(module)
            actual_res = call_for_per_sample_grads(test_module, loss_reduction="sum")(
                input
            ).sum()
            actual_res.backward()
            actual_grads = []
            for param in module.parameters():
                actual_grads.append(param.grad_sample)
                del param.grad_sample
            if diff_input:
                actual_grads.append(input.grad.clone())
                input.grad = torch.zeros_like(input.grad)

            # get per sample grads with a for loop, running over the input twice
            expected_grads = []
            for i in range(batch_size):
                input_slice = input[i]
                diff_params = module.parameters()
                if diff_input:
                    diff_params = chain(diff_params, (input_slice,))
                res = module(input_slice.unsqueeze(0)).sum()
                out_grads = torch.autograd.grad(
                    res, diff_params, torch.ones_like(res), allow_unused=True
                )
                expected_grads.append(out_grads)
        expected_grads = tuple(torch.stack(grad) for grad in zip(*expected_grads))
        expected_grads = tuple(
            expected_grad
            for expected_grad in expected_grads
            if expected_grad is not None
        )
        for actual, expected in zip(actual_grads, expected_grads):
            self.assertEqual(actual, 2 * expected)