def register_autograd(
    op: _op_identifier,
    backward: Callable,
    /,
    *,
    setup_context: Callable | None = None,
    lib=None,
) -> None:
    r"""Register a backward formula for this custom op.

    In order for an operator to work with autograd, you need to register
    a backward formula:
    1. You must tell us how to compute gradients during the backward pass
    by providing us a "backward" function.
    2. If you need any values from the forward to compute gradients, you can
    use `setup_context` to save values for backward.

    ``backward`` runs during the backward pass. It accepts ``(ctx, *grads)``:
    - ``grads`` is one or more gradients. The number of gradients matches
    the number of outputs of the operator.
    The ``ctx`` object is `the same ctx object <context_method_mixins>`_ used by
    :class:`torch.autograd.Function`. The semantics of ``backward_fn`` are the
    same as :meth:`torch.autograd.Function.backward`.

    ``setup_context(ctx, inputs, output)`` runs during the forward pass.
    Please save quantities needed for backward onto the ``ctx`` object via
    either :meth:`torch.autograd.function.FunctionCtx.save_for_backward`
    or assigning them as attributes of ``ctx``. If your custom op has
    kwarg-only arguments, we expect the signature of ``setup_context``
    to be ``setup_context(ctx, inputs, keyword_only_inputs, output)``.

    Both ``setup_context_fn`` and ``backward_fn`` must be traceable. That is,
    they may not directly access :meth:`torch.Tensor.data_ptr` and they must
    not depend on or mutate global state. If you need a non-traceable backward,
    you can make it a separate custom_op that you call inside ``backward_fn``.

    If you need different autograd behavior on different devices, then we
    recommend creating two different custom operators, one for each device
    that needs different behavior, and switching between them at runtime.

    Examples:
        >>> import torch
        >>> import numpy as np
        >>> from torch import Tensor
        >>>
        >>> @torch.library.custom_op("mylib::numpy_sin", mutates_args=())
        >>> def numpy_sin(x: Tensor) -> Tensor:
        >>>     x_np = x.cpu().numpy()
        >>>     y_np = np.sin(x_np)
        >>>     return torch.from_numpy(y_np).to(device=x.device)
        >>>
        >>> def setup_context(ctx, inputs, output) -> Tensor:
        >>>     x, = inputs
        >>>     ctx.save_for_backward(x)
        >>>
        >>> def backward(ctx, grad):
        >>>     x, = ctx.saved_tensors
        >>>     return grad * x.cos()
        >>>
        >>> torch.library.register_autograd(
        ...     "mylib::numpy_sin", backward, setup_context=setup_context
        ... )
        >>>
        >>> x = torch.randn(3, requires_grad=True)
        >>> y = numpy_sin(x)
        >>> (grad_x,) = torch.autograd.grad(y, x, torch.ones_like(y))
        >>> assert torch.allclose(grad_x, x.cos())
        >>>
        >>> # Example with a keyword-only arg
        >>> @torch.library.custom_op("mylib::numpy_mul", mutates_args=())
        >>> def numpy_mul(x: Tensor, *, val: float) -> Tensor:
        >>>     x_np = x.cpu().numpy()
        >>>     y_np = x_np * val
        >>>     return torch.from_numpy(y_np).to(device=x.device)
        >>>
        >>> def setup_context(ctx, inputs, keyword_only_inputs, output) -> Tensor:
        >>>     ctx.val = keyword_only_inputs["val"]
        >>>
        >>> def backward(ctx, grad):
        >>>     return grad * ctx.val
        >>>
        >>> torch.library.register_autograd(
        ...     "mylib::numpy_mul", backward, setup_context=setup_context
        ... )
        >>>
        >>> x = torch.randn(3, requires_grad=True)
        >>> y = numpy_mul(x, val=3.14)
        >>> (grad_x,) = torch.autograd.grad(y, x, torch.ones_like(y))
        >>> assert torch.allclose(grad_x, torch.full_like(x, 3.14))

    """
    if not isinstance(
        op, (str, torch._ops.OpOverload, torch._library.custom_ops.CustomOpDef)
    ):
        raise ValueError(
            f"register_autograd({op}): got unexpected type for op: {type(op)}"
        )
    if isinstance(op, torch._ops.OpOverload):
        op = op._name
    opdef = _maybe_get_opdef(op)
    if opdef is not None:
        opdef.register_autograd(backward, setup_context=setup_context)
        return

    if not isinstance(op, str):
        raise AssertionError(f"op must be str at this point, got {type(op).__name__}")
    qualname = op
    op = torch._library.utils.lookup_op(qualname)
    schema = op._schema
    if not _library.utils.is_functional_schema(schema):
        raise RuntimeError(
            f"Cannot register autograd formula for non-functional operator "
            f"{op} with schema {schema}. Please create "
            f"a functional operator and register an autograd formula for that."
        )
    if _library.utils.has_kwarg_only_tensors(schema):
        raise NotImplementedError(
            f"register_autograd with kwarg-only Tensor args. In the original "
            f"definition of the op, please make your tensors not kwarg-only. "
            f"Got: {schema}"
        )

    info = _library.autograd.Info(backward, setup_context)
    autograd_kernel = _library.autograd.make_autograd_impl(op, info)
    namespace, opname = torch._library.utils.parse_namespace(qualname)
    if lib is None:
        lib = Library(namespace, "FRAGMENT")
        _keep_alive.append(lib)
    lib.impl(opname, autograd_kernel, "Autograd", with_keyset=True)