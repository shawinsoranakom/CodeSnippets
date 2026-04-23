def _compare_ew_and_for_loop_per_sample_grads(self, op, sample_input, reduction):
        input = sample_input.input
        args = sample_input.args
        kwargs = sample_input.kwargs
        batch_size = input.shape[0] if len(input.shape) > 1 else 1

        # get per sample grads with ExpandedWeights objects
        loss_reduction = "sum" if reduction == torch.sum else "mean"
        (ew_input, ew_args, ew_kwargs) = make_expanded_weight(
            sample_input, batch_size, loss_reduction
        )
        diff_input_list = (ew_input,) + tuple(ew_args) + tuple(ew_kwargs.values())
        diff_input_list = [i for i in diff_input_list if is_diff_tensor(i)]
        diff_input_list = [
            i.orig_weight if isinstance(i, ExpandedWeight) else i
            for i in diff_input_list
        ]
        if not diff_input_list:
            return
        result = run_op(op, ew_input, *ew_args, **ew_kwargs)
        reduction(
            result
        ).backward()  # grad doesn't work with ExpandedWeight because it calls __torch_function__
        expanded_weight_grad = tuple(
            i.grad_sample if hasattr(i, "grad_sample") else i.grad
            for i in diff_input_list
        )

        # get per sample grads with for loop
        func = partial(run_op, op)

        per_sample_grad = for_loop_per_sample_grad(
            batch_size, reduction, input, func, *args, **kwargs
        )

        # check equality
        self.assertEqual(len(per_sample_grad), len(expanded_weight_grad))
        if loss_reduction == "mean":
            # don't check equality of `input.grad`s since these vanilla tensors won't be scaled
            expanded_weight_grad = expanded_weight_grad[1:]
            per_sample_grad = per_sample_grad[1:]
        for result_grad, expected_grad in zip(expanded_weight_grad, per_sample_grad):
            self.assertEqual(result_grad, expected_grad)