def wrapped(*args: Any, **kwargs: Any) -> Any:
        try:
            func_level = _func_increment_nesting(reapply_views)
            func_args = _wrap_all_tensors_to_functional(args, func_level)
            func_kwargs = _wrap_all_tensors_to_functional(kwargs, func_level)

            flattened_unwrapped_args = pytree.arg_tree_leaves(*args)
            flattened_wrapped_args = pytree.arg_tree_leaves(*func_args)
            flattened_unwrapped_kwargs = pytree.arg_tree_leaves(**kwargs)
            flattened_wrapped_kwargs = pytree.arg_tree_leaves(**func_kwargs)

            func_outputs = func(*func_args, **func_kwargs)
            outputs = _unwrap_all_tensors_from_functional(
                func_outputs, reapply_views=reapply_views
            )

            for a in flattened_wrapped_args + flattened_wrapped_kwargs:
                if isinstance(a, torch.Tensor):
                    # Call sync_() on the inputs, to ensure that any pending mutations have been applied.
                    torch._sync(a)

            # And if any mutations were applied to the inputs, we need to propagate them back to the user.
            for unwrapped, wrapped in zip(
                flattened_unwrapped_args, flattened_wrapped_args
            ):
                if isinstance(unwrapped, torch.Tensor) and isinstance(
                    wrapped, torch.Tensor
                ):
                    _propagate_functional_input_mutation(unwrapped, wrapped)
            for unwrapped, wrapped in zip(
                flattened_unwrapped_kwargs, flattened_wrapped_kwargs
            ):
                if isinstance(unwrapped, torch.Tensor) and isinstance(
                    wrapped, torch.Tensor
                ):
                    _propagate_functional_input_mutation(unwrapped, wrapped)

            return outputs
        finally:
            _func_decrement_nesting()