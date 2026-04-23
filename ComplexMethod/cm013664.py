def pad(
    input: Tensor,
    pad: list[int],
    mode: str = "constant",
    value: float | None = None,
) -> Tensor:
    r"""
    pad(input, pad, mode="constant", value=None) -> Tensor

    Pads tensor.

    Padding size:
        The padding size by which to pad some dimensions of :attr:`input`
        are described starting from the last dimension and moving forward.
        :math:`\left\lfloor\frac{\text{len(pad)}}{2}\right\rfloor` dimensions
        of ``input`` will be padded.
        For example, to pad only the last dimension of the input tensor, then
        :attr:`pad` has the form
        :math:`(\text{padding\_left}, \text{padding\_right})`;
        to pad the last 2 dimensions of the input tensor, then use
        :math:`(\text{padding\_left}, \text{padding\_right},`
        :math:`\text{padding\_top}, \text{padding\_bottom})`;
        to pad the last 3 dimensions, use
        :math:`(\text{padding\_left}, \text{padding\_right},`
        :math:`\text{padding\_top}, \text{padding\_bottom}`
        :math:`\text{padding\_front}, \text{padding\_back})`.

    Padding mode:
        See :class:`torch.nn.CircularPad2d`, :class:`torch.nn.ConstantPad2d`,
        :class:`torch.nn.ReflectionPad2d`, and :class:`torch.nn.ReplicationPad2d`
        for concrete examples on how each of the padding modes works. Constant
        padding is implemented for arbitrary dimensions. Circular, replicate and
        reflection padding are implemented for padding the last 3 dimensions of a
        4D or 5D input tensor, the last 2 dimensions of a 3D or 4D input tensor,
        or the last dimension of a 2D or 3D input tensor.

    Note:
        When using the CUDA backend, this operation may induce nondeterministic
        behaviour in its backward pass that is not easily switched off.
        Please see the notes on :doc:`/notes/randomness` for background.

    Args:
        input (Tensor): N-dimensional tensor
        pad (tuple): m-elements tuple, where
            :math:`\frac{m}{2} \leq` input dimensions and :math:`m` is even.
        mode: ``'constant'``, ``'reflect'``, ``'replicate'`` or ``'circular'``.
            Default: ``'constant'``
        value: fill value for ``'constant'`` padding. Default: ``0``

    Examples::

        >>> t4d = torch.empty(3, 3, 4, 2)
        >>> p1d = (1, 1) # pad last dim by 1 on each side
        >>> out = F.pad(t4d, p1d, "constant", 0)  # effectively zero padding
        >>> print(out.size())
        torch.Size([3, 3, 4, 4])
        >>> p2d = (1, 1, 2, 2) # pad last dim by (1, 1) and 2nd to last by (2, 2)
        >>> out = F.pad(t4d, p2d, "constant", 0)
        >>> print(out.size())
        torch.Size([3, 3, 8, 4])
        >>> t4d = torch.empty(3, 3, 4, 2)
        >>> p3d = (0, 1, 2, 1, 3, 3) # pad by (0, 1), (2, 1), and (3, 3)
        >>> out = F.pad(t4d, p3d, "constant", 0)
        >>> print(out.size())
        torch.Size([3, 9, 7, 3])
    """
    if has_torch_function_unary(input):
        return handle_torch_function(
            torch.nn.functional.pad, (input,), input, pad, mode=mode, value=value
        )
    if not torch.jit.is_scripting():
        if torch.are_deterministic_algorithms_enabled() and (
            input.is_cuda or input.is_xpu
        ):
            if mode == "replicate":
                # Use slow decomp whose backward will be in terms of index_put.
                if torch.compiler.is_compiling():
                    # nonstrict_trace makes Dynamo skip the function body
                    # (which contains Dynamo-untraceable code) while
                    # AOTAutograd still traces into it for the backward.
                    return torch._dynamo.decorators.nonstrict_trace(
                        torch._decomp.decompositions._replication_pad
                    )(input, pad)
                # importlib is required because the import cannot be top level
                # (cycle) and cannot be nested (TS doesn't support)
                return importlib.import_module(
                    "torch._decomp.decompositions"
                )._replication_pad(input, pad)
    return torch._C._nn.pad(input, pad, mode, value)