def _do_test(
        self,
        module,
        input,
        args=None,
        kwargs=None,
        batch_first=True,
        atol=None,
        rtol=None,
    ):
        args = args or ()
        kwargs = kwargs or {}

        batch_dim = 0 if batch_first else 1
        batch_size = input.shape[batch_dim]
        diff_input = input.dtype == torch.float or input.dtype == torch.double
        if diff_input:
            input.requires_grad_()

        with freeze_rng_state():
            # get per sample grads with ExpandedWeights context manager
            actual_res = call_for_per_sample_grads(
                module,
                batch_size=batch_size,
                loss_reduction="sum",
                batch_first=batch_first,
            )(input, *args, **kwargs).sum()
            actual_res.backward()
            actual_grads = []
            for param in module.parameters():
                actual_grads.append(param.grad_sample)
                del param.grad_sample
            if diff_input:
                actual_grads.append(input.grad.clone())
                input.grad = torch.zeros_like(input.grad)

            # get per sample grads with a for loop
            expected_res = torch.tensor(
                0.0, device=input.device, dtype=actual_res.dtype
            )
            expected_grads = []
            for i in range(batch_size):
                input_slice = input.narrow(batch_dim, i, 1)
                input_slice = input_slice.squeeze(batch_dim)

                # h's batch dim is always the first dim. Must be contiguous for CUDA
                sliced_args = tree_map_only(
                    torch.Tensor, lambda t: t.narrow(1, i, 1).contiguous(), args
                )
                diff_params = module.parameters()
                if diff_input:
                    diff_params = chain(diff_params, (input_slice,))
                res = module(
                    input_slice.unsqueeze(batch_dim).contiguous(),
                    *sliced_args,
                    **kwargs,
                ).sum()
                out_grads = torch.autograd.grad(
                    res, diff_params, torch.ones_like(res), allow_unused=True
                )
                expected_grads.append(out_grads)
                expected_res += res
            expected_grads = [torch.stack(grad) for grad in zip(*expected_grads)]
            if not batch_first:
                expected_grads[-1] = expected_grads[-1].transpose(0, 1)
        self.assertEqual(actual_res, expected_res, atol=atol, rtol=rtol)
        [
            self.assertEqual(actual, expected, atol=atol, rtol=rtol)
            for (actual, expected) in zip(actual_grads, expected_grads)
        ]