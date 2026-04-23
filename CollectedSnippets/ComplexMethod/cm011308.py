def step(
        self,
        *args,
        target=None,
        losses: list | None = None,
        return_outputs: bool = True,
        **kwargs,
    ):
        """
        Run one iteration of the pipeline schedule with *whole-batch* input.
        Will chunk the input into microbatches automatically, and go through the
        microbatches according to the schedule implementation.

        args: positional arguments to the model (as in non-pipeline case).
        kwargs: keyword arguments to the model (as in non-pipeline case).
        target: target for the loss function.
        losses: a list to store the losses for each microbatch.
        return_outputs: whether to return the outputs from the last stage.
        """
        if (
            self._has_backward
            and self._backward_requires_autograd
            and not torch.is_grad_enabled()
        ):
            raise RuntimeError(
                "step() requires gradients to be enabled for backward computation; "
                "it should not be used under torch.no_grad() context. "
                "Please call eval() instead."
            )

        # Set the same has_backward flag for stage object
        for stage in self._stages:
            stage.has_backward = self._has_backward

        # Clean per iteration
        for stage in self._stages:
            stage.clear_runtime_states()

        # Split inputs into microbatches
        args_split, kwargs_split = self._split_inputs(args, kwargs)

        # Split target into microbatches
        if target is not None:
            targets_split = list(torch.tensor_split(target, self._n_microbatches))
        else:
            targets_split = None

        # Run microbatches
        self._step_microbatches(
            args_split, kwargs_split, targets_split, losses, return_outputs
        )

        # Return merged results per original format
        for stage in self._stages:
            if stage.is_last and return_outputs:
                return self._merge_outputs(stage.output_chunks)
        # Does not contain the last stage or we do not return output chunks
        return None