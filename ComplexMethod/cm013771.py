def register_parametrization(
    module: Module,
    tensor_name: str,
    parametrization: Module,
    *,
    unsafe: bool = False,
) -> Module:
    r"""Register a parametrization to a tensor in a module.

    Assume that ``tensor_name="weight"`` for simplicity. When accessing ``module.weight``,
    the module will return the parametrized version ``parametrization(module.weight)``.
    If the original tensor requires a gradient, the backward pass will differentiate
    through :attr:`parametrization`, and the optimizer will update the tensor accordingly.

    The first time that a module registers a parametrization, this function will add an attribute
    ``parametrizations`` to the module of type :class:`~ParametrizationList`.

    The list of parametrizations on the tensor ``weight`` will be accessible under
    ``module.parametrizations.weight``.

    The original tensor will be accessible under
    ``module.parametrizations.weight.original``.

    Parametrizations may be concatenated by registering several parametrizations
    on the same attribute.

    The training mode of a registered parametrization is updated on registration
    to match the training mode of the host module

    Parametrized parameters and buffers have an inbuilt caching system that can be activated
    using the context manager :func:`cached`.

    A :attr:`parametrization` may optionally implement a method with signature

    .. code-block:: python

        def right_inverse(self, X: Tensor) -> Union[Tensor, Sequence[Tensor]]

    This method is called on the unparametrized tensor when the first parametrization
    is registered to compute the initial value of the original tensor.
    If this method is not implemented, the original tensor will be just the unparametrized tensor.

    If all the parametrizations registered on a tensor implement `right_inverse` it is possible
    to initialize a parametrized tensor by assigning to it, as shown in the example below.

    It is possible for the first parametrization to depend on several inputs.
    This may be implemented returning a tuple of tensors from ``right_inverse``
    (see the example implementation of a ``RankOne`` parametrization below).

    In this case, the unconstrained tensors are also located under ``module.parametrizations.weight``
    with names ``original0``, ``original1``,...

    .. note::

        If unsafe=False (default) both the forward and right_inverse methods will be called
        once to perform a number of consistency checks.
        If unsafe=True, then right_inverse will be called if the tensor is not parametrized,
        and nothing will be called otherwise.

    .. note::

        In most situations, ``right_inverse`` will be a function such that
        ``forward(right_inverse(X)) == X`` (see
        `right inverse <https://en.wikipedia.org/wiki/Inverse_function#Right_inverses>`_).
        Sometimes, when the parametrization is not surjective, it may be reasonable
        to relax this.

    .. warning::

        If a parametrization depends on several inputs, :func:`~register_parametrization`
        will register a number of new parameters. If such parametrization is registered
        after the optimizer is created, these new parameters will need to be added manually
        to the optimizer. See :meth:`torch.Optimizer.add_param_group`.

    Args:
        module (nn.Module): module on which to register the parametrization
        tensor_name (str): name of the parameter or buffer on which to register
            the parametrization
        parametrization (nn.Module): the parametrization to register
    Keyword args:
        unsafe (bool): a boolean flag that denotes whether the parametrization
            may change the dtype and shape of the tensor. Default: `False`
            Warning: the parametrization is not checked for consistency upon registration.
            Enable this flag at your own risk.

    Raises:
        ValueError: if the module does not have a parameter or a buffer named :attr:`tensor_name`

    Examples:
        >>> # xdoctest: +REQUIRES(env:TORCH_DOCTEST_LAPACK)
        >>> import torch
        >>> import torch.nn as nn
        >>> import torch.nn.utils.parametrize as P
        >>>
        >>> class Symmetric(nn.Module):
        >>>     def forward(self, X):
        >>>         return X.triu() + X.triu(1).T  # Return a symmetric matrix
        >>>
        >>>     def right_inverse(self, A):
        >>>         return A.triu()
        >>>
        >>> m = nn.Linear(5, 5)
        >>> P.register_parametrization(m, "weight", Symmetric())
        >>> print(torch.allclose(m.weight, m.weight.T))  # m.weight is now symmetric
        True
        >>> A = torch.rand(5, 5)
        >>> A = A + A.T  # A is now symmetric
        >>> m.weight = A  # Initialize the weight to be the symmetric matrix A
        >>> print(torch.allclose(m.weight, A))
        True

        >>> class RankOne(nn.Module):
        >>>     def forward(self, x, y):
        >>> # Form a rank 1 matrix multiplying two vectors
        >>>         return x.unsqueeze(-1) @ y.unsqueeze(-2)
        >>>
        >>>     def right_inverse(self, Z):
        >>> # Project Z onto the rank 1 matrices
        >>>         U, S, Vh = torch.linalg.svd(Z, full_matrices=False)
        >>> # Return rescaled singular vectors
        >>>         s0_sqrt = S[0].sqrt().unsqueeze(-1)
        >>>         return U[..., :, 0] * s0_sqrt, Vh[..., 0, :] * s0_sqrt
        >>>
        >>> linear_rank_one = P.register_parametrization(
        ...     nn.Linear(4, 4), "weight", RankOne()
        ... )
        >>> print(torch.linalg.matrix_rank(linear_rank_one.weight).item())
        1

    """
    parametrization.train(module.training)
    if is_parametrized(module, tensor_name):
        # Correctness checks.
        # If A is the space of tensors with shape and dtype equal to module.weight
        # we check that parametrization.forward and parametrization.right_inverse are
        # functions from A to A
        if not unsafe:
            Y = getattr(module, tensor_name)
            X = parametrization(Y)
            if not isinstance(X, Tensor):
                raise ValueError(
                    f"A parametrization must return a tensor. Got {type(X).__name__}."
                )
            if X.dtype != Y.dtype:
                raise ValueError(
                    "Registering a parametrization may not change the dtype of the tensor, unless the `unsafe` flag is enabled.\n"
                    f"module.{tensor_name}.dtype: {Y.dtype}\n"
                    f"parametrization(module.{tensor_name}).dtype: {X.dtype}"
                )
            if X.shape != Y.shape:
                raise ValueError(
                    "Registering a parametrization may not change the shape of the tensor, unless the `unsafe` flag is enabled.\n"
                    f"module.{tensor_name}.shape: {Y.shape}\n"
                    f"parametrization(module.{tensor_name}).shape: {X.shape}"
                )
            if hasattr(parametrization, "right_inverse"):
                try:
                    Z = parametrization.right_inverse(X)  # type: ignore[operator]
                except NotImplementedError:
                    pass
                else:
                    if not isinstance(Z, Tensor):
                        raise ValueError(
                            f"parametrization.right_inverse must return a tensor. Got: {type(Z).__name__}"
                        )
                    if Z.dtype != Y.dtype:
                        raise ValueError(
                            "The tensor returned by parametrization.right_inverse must have the same dtype "
                            f"as module.{tensor_name}, unless the `unsafe` flag is enabled.\n"
                            f"module.{tensor_name}.dtype: {Y.dtype}\n"
                            f"returned dtype: {Z.dtype}"
                        )
                    if Z.shape != Y.shape:
                        raise ValueError(
                            "The tensor returned by parametrization.right_inverse must have the same shape "
                            f"as module.{tensor_name}, unless the `unsafe` flag is enabled.\n"
                            f"module.{tensor_name}.shape: {Y.shape}\n"
                            f"returned shape: {Z.shape}"
                        )
            # else right_inverse is assumed to be the identity

        # add the new parametrization to the parametrization list
        if not isinstance(module.parametrizations, ModuleDict):
            raise AssertionError(
                f"Expected module.parametrizations to be a ModuleDict, "
                f"got {type(module.parametrizations).__name__}"
            )
        module.parametrizations[tensor_name].append(parametrization)  # type: ignore[operator]
        # If unsafe was True in previous parametrization, keep it enabled
        module.parametrizations[tensor_name].unsafe |= unsafe  # type: ignore[index, union-attr, operator]
    elif tensor_name in module._buffers or tensor_name in module._parameters:
        # Set the parametrization mechanism
        # Fetch the original buffer or parameter
        original = getattr(module, tensor_name)
        # We create this early to check for possible errors
        parametrizations = ParametrizationList(
            [parametrization], original, unsafe=unsafe
        )
        # Delete the previous parameter or buffer
        delattr(module, tensor_name)
        # If this is the first parametrization registered on the module,
        # we prepare the module to inject the property
        if not is_parametrized(module):
            # Change the class
            _inject_new_class(module)
            # Inject a ``ModuleDict`` into the instance under module.parametrizations
            module.parametrizations = ModuleDict()
        # Add a property into the class
        _inject_property(module, tensor_name)
        # Add a ParametrizationList
        if not isinstance(module.parametrizations, ModuleDict):
            raise AssertionError(
                f"Expected module.parametrizations to be a ModuleDict, "
                f"got {type(module.parametrizations).__name__}"
            )
        module.parametrizations[tensor_name] = parametrizations
    else:
        raise ValueError(
            f"Module '{module}' does not have a parameter, a buffer, or a "
            f"parametrized element with name '{tensor_name}'"
        )
    return module