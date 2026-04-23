def gradgradcheck(
    func: Callable[..., _TensorOrTensors],  # See Note [VarArg of Tensors]
    inputs: _TensorOrTensors,
    grad_outputs: _TensorOrOptionalTensors | None = None,
    *,
    eps: float = 1e-6,
    atol: float = 1e-5,
    rtol: float = 1e-3,
    gen_non_contig_grad_outputs: bool = False,
    raise_exception: bool = True,
    nondet_tol: float = 0.0,
    check_undefined_grad: bool = True,
    check_grad_dtypes: bool = False,
    check_batched_grad: bool = False,
    check_fwd_over_rev: bool = False,
    check_rev_over_rev: bool = True,
    fast_mode: bool = False,
    masked: bool = False,
) -> bool:
    r"""Check gradients of gradients computed via small finite differences
    against analytical gradients wrt tensors in :attr:`inputs` and
    :attr:`grad_outputs` that are of floating point or complex type and with
    ``requires_grad=True``.

    This function checks that backpropagating through the gradients computed
    to the given :attr:`grad_outputs` are correct.

    The check between numerical and analytical gradients uses :func:`~torch.allclose`.

    .. note::
        The default values are designed for :attr:`input` and
        :attr:`grad_outputs` of double precision. This check will likely fail if
        they are of less precision, e.g., ``FloatTensor``.

    .. warning::
       If any checked tensor in :attr:`input` and :attr:`grad_outputs` has
       overlapping memory, i.e., different indices pointing to the same memory
       address (e.g., from :func:`torch.Tensor.expand`), this check will likely fail
       because the numerical gradients computed by point perturbation at such
       indices will change values at all other indices that share the same
       memory address.

    Args:
        func (function): a Python function that takes Tensor inputs and returns
            a Tensor or a tuple of Tensors
        inputs (tuple of Tensor or Tensor): inputs to the function
        grad_outputs (tuple of [Tensor or None] or Tensor, optional): The gradients with
            respect to the function's outputs.
        eps (float, optional): perturbation for finite differences
        atol (float, optional): absolute tolerance
        rtol (float, optional): relative tolerance
        gen_non_contig_grad_outputs (bool, optional): if :attr:`grad_outputs` is
            ``None`` and :attr:`gen_non_contig_grad_outputs` is ``True``, the
            randomly generated gradient outputs are made to be noncontiguous
        raise_exception (bool, optional): indicating whether to raise an exception if
            the check fails. The exception gives more information about the
            exact nature of the failure. This is helpful when debugging gradchecks.
        nondet_tol (float, optional): tolerance for non-determinism. When running
            identical inputs through the differentiation, the results must either match
            exactly (default, 0.0) or be within this tolerance. Note that a small amount
            of nondeterminism in the gradient will lead to larger inaccuracies in
            the second derivative.
        check_undefined_grad (bool, optional): if True, check if undefined output grads
            are supported and treated as zeros
        check_batched_grad (bool, optional): if True, check if we can compute
            batched gradients using prototype vmap support. Defaults to False.
        fast_mode (bool, optional): if True, run a faster implementation of gradgradcheck that
            no longer computes the entire jacobian.
        masked (bool, optional): if True, the gradients of unspecified elements of
            sparse tensors are ignored (default, False).
    Returns:
        True if all differences satisfy allclose condition
    """
    if not (check_fwd_over_rev or check_rev_over_rev):
        raise AssertionError(
            "Expected at least one of check_fwd_over_rev or check_rev_over_rev to be True"
        )
    if check_undefined_grad and not check_rev_over_rev:
        raise AssertionError(
            "Setting check_undefined_grad=True requires check_rev_over_rev to be True"
        )
    if check_batched_grad and not check_rev_over_rev:
        raise AssertionError(
            "Setting check_batched_grad=True requires check_rev_over_rev to be True"
        )
    # TODO: do we want to test this too?
    # assert not (check_batched_forward_grad and not check_fwd_over_rev), (
    #     "Setting check_batched_forward_grad=True requires check_fwd_over_rev to be True")
    tupled_inputs = _as_tuple(inputs)

    if grad_outputs is None:
        # If grad_outputs is not specified, create random Tensors of the same shape, type, and device as the outputs

        outputs = _differentiable_outputs(func(*tupled_inputs))
        tupled_grad_outputs = tuple(
            torch.testing.make_tensor(
                x.shape,
                dtype=x.dtype
                if x.is_floating_point() or x.is_complex()
                else torch.double,
                device=x.device,
                low=-1,
                high=1,
                requires_grad=True,
                noncontiguous=gen_non_contig_grad_outputs,
            )
            for x in outputs
        )
    else:
        tupled_grad_outputs = _as_tuple(grad_outputs)

    num_outputs = len(tupled_grad_outputs)

    # NB: We need to save the requires_grad information about the inputs here because gradcheck detaches inputs
    #     before running forward mode AD
    diff_input_args_indices = {
        i for i, x in enumerate(tupled_inputs) if is_tensor_like(x) and x.requires_grad
    }
    diff_grad_output_indices = {
        i for i, x in enumerate(tupled_grad_outputs) if x.requires_grad
    }

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

    return gradcheck(
        new_func,
        tupled_inputs + tupled_grad_outputs,
        eps=eps,
        atol=atol,
        rtol=rtol,
        raise_exception=raise_exception,
        nondet_tol=nondet_tol,
        check_undefined_grad=check_undefined_grad,
        check_grad_dtypes=check_grad_dtypes,
        check_batched_grad=check_batched_grad,
        fast_mode=fast_mode,
        check_forward_ad=check_fwd_over_rev,
        check_backward_ad=check_rev_over_rev,
        masked=masked,
    )