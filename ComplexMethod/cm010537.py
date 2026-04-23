def _get_numerical_jacobian(
    fn, inputs, outputs=None, target=None, eps=1e-3, is_forward_ad=False
) -> list[tuple[torch.Tensor, ...]]:
    """Compute the numerical Jacobian of `fn(inputs)` with respect to `target`.

    If not specified, targets are the input. Returns M * N Jacobians where N is the
    number of tensors in target that require grad and M is the number of non-integral
    outputs.

    Args:
        fn: the function to compute the jacobian for
        inputs: inputs to `fn`
        outputs: provide precomputed outputs to avoid one extra invocation of fn
        target: the Tensors wrt whom Jacobians are calculated (default=`inputs`)
        eps: the magnitude of the perturbation during finite differencing
             (default=`1e-3`)
        is_forward_ad: if this numerical jacobian is computed to be checked wrt
                       forward AD gradients (this is used for error checking only)

    Returns:
        A list of M N-tuples of tensors

    Note that `target` may not even be part of `input` to `fn`, so please be
    **very careful** in this to not clone `target`.
    """
    jacobians: list[tuple[torch.Tensor, ...]] = []
    if outputs is None:
        outputs = _as_tuple(fn(*_as_tuple(inputs)))
    if not is_forward_ad and any(o.is_complex() for o in outputs):
        raise ValueError(
            "Expected output to be non-complex. get_numerical_jacobian no "
            "longer supports functions that return complex outputs."
        )
    if target is None:
        target = inputs
    inp_indices = [
        i for i, a in enumerate(target) if is_tensor_like(a) and a.requires_grad
    ]
    for inp, inp_idx in zip(_iter_tensors(target, True), inp_indices):
        jacobians += [
            get_numerical_jacobian_wrt_specific_input(
                fn,
                inp_idx,
                inputs,
                outputs,
                eps,
                input=inp,
                is_forward_ad=is_forward_ad,
            )
        ]
    return jacobians