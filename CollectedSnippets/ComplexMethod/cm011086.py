def _post_backward_use_sharded_grad_views(handle: FlatParamHandle):
    if not handle._use_orig_params:
        return
    # Since the handle's `FlatParameter` completed its gradient computation, we
    # should reset the gradient noneness mask
    handle._reset_is_grad_none()
    # Delay using sharded gradient views until after the reduce-scatter instead
    # of immediately after resharding
    handle._use_sharded_grad_views()
    if handle._has_optim_in_backward:
        handle.prepare_gradient_for_optim()
        for orig_param in handle.flat_param._params:
            # Check for `None` gradient to filter parameters not in the rank
            if orig_param.grad is not None and hasattr(
                orig_param, "_in_backward_optimizers"
            ):
                # TODO (rohan-varma): For CPU offload, this unfortunately
                # operates on CPU because the parameters and gradients have
                # already been offloaded. We should run this on GPU after
                # refactoring.
                for optim in orig_param._in_backward_optimizers:
                    optim.step()

                optim.zero_grad(set_to_none=True)
        handle._reset_flat_param_grad_info_if_needed()
        if handle._offload_params:
            handle.flat_param._cpu_grad = None