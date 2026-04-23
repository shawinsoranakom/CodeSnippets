def custom_gradient_checkpointing_func(func: Callable, *args: Union["torch.Tensor", Any], **kwargs):
        if isinstance(func, partial):
            module: torch.nn.Module = func.func.__self__
        else:
            module: torch.nn.Module = func.__self__

        has_grad = False
        if any(param.requires_grad for param in module.parameters()):
            has_grad = True
            for arg in args:
                if torch.is_tensor(arg) and torch.is_floating_point(arg):
                    arg.requires_grad_(True)
                    break  # assume the first tensor is always the hidden states

        if has_grad:
            return gradient_checkpointing_func(func, *args, **kwargs)
        else:
            return func(*args, **kwargs)