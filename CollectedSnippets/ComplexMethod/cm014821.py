def _do_test_rnn_packed_sequence(
        self, module, input, args=None, kwargs=None, atol=None, rtol=None
    ):
        args = args if args is not None else ()
        kwargs = kwargs if kwargs is not None else {}

        batch_size = max(tuple(input.batch_sizes)).item()

        with freeze_rng_state():
            # get per sample grads with ExpandedWeights context manager
            actual_res = call_for_per_sample_grads(
                module, batch_size=batch_size, loss_reduction="sum"
            )(input, *args, **kwargs).data.sum()
            actual_res.backward()
            actual_grads = []
            for param in module.parameters():
                self.assertEqual(param.grad_sample.shape[0], batch_size)
                actual_grads.append(param.grad_sample)
                del param.grad_sample

            input.data.grad = torch.zeros_like(input.data)

            # compute the per sample grads with a for loop
            expected_res = torch.zeros_like(actual_res)
            expected_grads = []
            padded_input, seq_sizes = torch.nn.utils.rnn.pad_packed_sequence(
                input, batch_first=True
            )
            for i in range(len(seq_sizes)):
                input_slice = padded_input[i].narrow(0, 0, seq_sizes[i])
                diff_params = module.parameters()
                batch_dim = 0 if module.m.batch_first else 1
                res = module(input_slice.unsqueeze(batch_dim), *args, **kwargs).sum()
                expected_res += res
                out_grads = torch.autograd.grad(
                    res, diff_params, torch.ones_like(res), allow_unused=True
                )
                expected_grads.append(out_grads)

            expected_grads = [torch.stack(grad) for grad in zip(*expected_grads)]
            self.assertEqual(actual_res, expected_res, atol=atol, rtol=rtol)
            [
                self.assertEqual(actual, expected, atol=atol, rtol=rtol)
                for (actual, expected) in zip(actual_grads, expected_grads)
            ]