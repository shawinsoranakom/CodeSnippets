def new_func(*args):
        # Restore the requires_grad information
        input_args = tuple(
            x.requires_grad_() if i in diff_input_args_indices else x
            for i, x in enumerate(args[:-num_outputs])
        )
        outputs = _differentiable_outputs(func(*input_args))
        grad_outputs = tuple(
            x.requires_grad_() if i in diff_grad_output_indices else x
            for i, x in enumerate(args[-num_outputs:])
        )
        diff_input_args = tuple(
            x for i, x in enumerate(input_args) if i in diff_input_args_indices
        )
        grad_inputs = torch.autograd.grad(
            outputs, diff_input_args, grad_outputs, create_graph=True, allow_unused=True
        )
        grad_inputs = tuple(g for g in grad_inputs if g is not None)
        return grad_inputs