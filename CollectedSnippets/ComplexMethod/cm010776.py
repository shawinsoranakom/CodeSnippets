def grad_and_value_impl(
    func: Callable[..., Any],
    argnums: argnums_t,
    has_aux: bool,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> tuple[Any, Any]:
    with grad_increment_nesting() as level:
        output, aux, grad_input = None, None, None
        # See NOTE [grad and vjp interaction with no_grad]
        with torch.enable_grad():
            args = _wrap_all_tensors(args, level)
            kwargs = _wrap_all_tensors(kwargs, level)
            diff_args = _slice_argnums(args, argnums, as_tuple=False)
            tree_map_(partial(_create_differentiable, level=level), diff_args)

            output = func(*args, **kwargs)
            if has_aux:
                if not (isinstance(output, tuple) and len(output) == 2):
                    raise RuntimeError(
                        "grad_and_value(f)(*args): output of function f should be a tuple: (output, aux) "
                        "if has_aux is True"
                    )
                output, aux = output

            if not isinstance(output, torch.Tensor):
                raise RuntimeError(
                    "grad_and_value(f)(*args): Expected f(*args) "
                    f"to return a Tensor, got {type(output)}"
                )
            if output.dim() != 0:
                raise RuntimeError(
                    "grad_and_value(f)(*args): Expected f(*args) "
                    "to return a scalar Tensor, got tensor with "
                    f"{output.dim()} dims. Maybe you wanted to "
                    "use the vjp or jacrev APIs instead?"
                )

            flat_diff_args, spec = tree_flatten(diff_args)

            # NB: need create_graph so that backward pass isn't run in no_grad mode
            flat_outputs = _as_tuple(output)
            flat_grad_input = _autograd_grad(
                flat_outputs, flat_diff_args, create_graph=True
            )
            grad_input = tree_unflatten(flat_grad_input, spec)

            grad_input = _undo_create_differentiable(grad_input, level)
            output = _undo_create_differentiable(output, level)
            if has_aux:
                # pyrefly: ignore[bad-specialization]
                aux = _undo_create_differentiable(aux, level)

        if has_aux:
            return grad_input, (output, aux)
        return grad_input, output