def tensordot(
    a,
    b,
    dims=2,
    out: torch.Tensor | None = None,
):
    r"""Returns a contraction of a and b over multiple dimensions.

    :attr:`tensordot` implements a generalized matrix product.

    Args:
      a (Tensor): Left tensor to contract
      b (Tensor): Right tensor to contract
      dims (int or Tuple[List[int], List[int]] or List[List[int]] containing two lists or Tensor): number of dimensions to
         contract or explicit lists of dimensions for :attr:`a` and
         :attr:`b` respectively

    When called with a non-negative integer argument :attr:`dims` = :math:`d`, and
    the number of dimensions of :attr:`a` and :attr:`b` is :math:`m` and :math:`n`,
    respectively, :func:`~torch.tensordot` computes the tensor :math:`r` of shape
    ``a.shape[:-dims] + b.shape[dims:]`` given by:

    .. math::
        r_{i_1,...,i_{m-d}, j_1,...,j_{n-d}}
          = \sum_{k_1,...,k_d} a_{i_1,...,i_{m-d},k_1,...,k_d} \times b_{k_1,...,k_d, j_1,...,j_{n-d}}.

    When called with :attr:`dims` of the list form, the given dimensions will be contracted
    in place of the last :math:`d` of :attr:`a` and the first :math:`d` of :math:`b`. The sizes
    in these dimensions must match, but :func:`~torch.tensordot` will deal with broadcasted
    dimensions.

    Examples::

        >>> a = torch.arange(60.).reshape(3, 4, 5)
        >>> b = torch.arange(24.).reshape(4, 3, 2)
        >>> torch.tensordot(a, b, dims=([1, 0], [0, 1]))
        tensor([[4400., 4730.],
                [4532., 4874.],
                [4664., 5018.],
                [4796., 5162.],
                [4928., 5306.]])

        >>> # xdoctest: +REQUIRES(env:TORCH_DOCTEST_CUDA)
        >>> a = torch.randn(3, 4, 5, device='cuda')
        >>> b = torch.randn(4, 5, 6, device='cuda')
        >>> c = torch.tensordot(a, b, dims=2).cpu()
        tensor([[ 8.3504, -2.5436,  6.2922,  2.7556, -1.0732,  3.2741],
                [ 3.3161,  0.0704,  5.0187, -0.4079, -4.3126,  4.8744],
                [ 0.8223,  3.9445,  3.2168, -0.2400,  3.4117,  1.7780]])

        >>> a = torch.randn(3, 5, 4, 6)
        >>> b = torch.randn(6, 4, 5, 3)
        >>> torch.tensordot(a, b, dims=([2, 1, 3], [1, 2, 0]))
        tensor([[  7.7193,  -2.4867, -10.3204],
                [  1.5513, -14.4737,  -6.5113],
                [ -0.2850,   4.2573,  -3.5997]])
    """
    if has_torch_function_variadic(a, b):
        return handle_torch_function(tensordot, (a, b), a, b, dims=dims, out=out)

    if not isinstance(dims, (tuple, list, torch.Tensor, int, torch.SymInt)):
        raise RuntimeError(
            "tensordot expects dims to be int or "
            + "tuple[list[int], list[int]] or "
            + "list[list[int]] containing two lists, but got "
            + f"dims={dims}"
        )

    dims_a: list[int] = []
    dims_b: list[int] = []

    if isinstance(dims, (tuple, list)):
        dims_a, dims_b = dims

    if isinstance(dims, torch.Tensor):
        num_elements = dims.numel()
        if num_elements > 1:
            if dims.size()[0] != 2:
                raise AssertionError(
                    f"dims tensor must have size 2 in first dimension, got {dims.size()[0]}"
                )
            dims_a = torch.jit.annotate(list[int], dims[0].tolist())
            dims_b = torch.jit.annotate(list[int], dims[1].tolist())
        else:
            dims_val = int(dims.item())
            if dims_val < 0:
                raise RuntimeError(f"tensordot expects dims >= 0, but got dims={dims}")
            dims_a = list(range(-dims_val, 0))
            dims_b = list(range(dims_val))

    if isinstance(dims, (int, torch.SymInt)):
        if dims < 0:
            raise RuntimeError(f"tensordot expects dims >= 0, but got dims={dims}")
        if dims > min(a.dim(), b.dim()):
            raise RuntimeError(
                f"tensordot expects dims < ndim_a or ndim_b, but got dims={dims}"
            )
        dims_a = list(range(-dims, 0))
        dims_b = list(range(dims))

    if out is None:
        return _VF.tensordot(a, b, dims_a, dims_b)  # type: ignore[attr-defined]
    else:
        return _VF.tensordot(a, b, dims_a, dims_b, out=out)