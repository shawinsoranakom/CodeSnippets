def remove_parametrizations(
    module: Module,
    tensor_name: str,
    leave_parametrized: bool = True,
) -> Module:
    r"""Remove the parametrizations on a tensor in a module.

    - If ``leave_parametrized=True``, ``module[tensor_name]`` will be set to
      its current output. In this case, the parametrization shall not change the ``dtype``
      of the tensor.
    - If ``leave_parametrized=False``, ``module[tensor_name]`` will be set to
      the unparametrised tensor in ``module.parametrizations[tensor_name].original``.
      This is only possible when the parametrization depends on just one tensor.

    Args:
        module (nn.Module): module from which remove the parametrization
        tensor_name (str): name of the parametrization to be removed
        leave_parametrized (bool, optional): leave the attribute :attr:`tensor_name` parametrized.
            Default: ``True``

    Returns:
        Module: module

    Raises:
        ValueError: if ``module[tensor_name]`` is not parametrized
        ValueError: if ``leave_parametrized=False`` and the parametrization depends on several tensors
    """
    if not is_parametrized(module, tensor_name):
        raise ValueError(
            f"Module {module} does not have a parametrization on {tensor_name}"
        )

    # Fetch the original tensor
    if not isinstance(module.parametrizations, ModuleDict):
        raise AssertionError(
            f"Expected module.parametrizations to be a ModuleDict, "
            f"got {type(module.parametrizations).__name__}"
        )
    parametrizations = module.parametrizations[tensor_name]

    if parametrizations.is_tensor:
        original = parametrizations.original
        if not isinstance(original, torch.Tensor):
            raise AssertionError(
                f"Expected original to be a Tensor (is_tensor promised us a Tensor), "
                f"got {type(original).__name__}"
            )
        if leave_parametrized:
            with torch.no_grad():
                t = getattr(module, tensor_name)
            # We know they have the same dtype because we have checked this when registering the
            # parametrizations. As such, we can use set_
            # We do this so that the parameter does not to change the id()
            # This way the user does not need to update the optimizer
            with torch.no_grad():
                if type(original) is torch.Tensor:
                    _maybe_set(original, t)
                else:
                    try:
                        _maybe_set(original, t)
                    except RuntimeError as e:
                        # TODO: Fix this for tensor subclasses that are parameters:
                        # RuntimeError: set_storage is not allowed on a Tensor created from .data or .detach().
                        raise RuntimeError(
                            "Calling remove_parametrizations() with leave_parametrized=True "
                            "for a parameter that is an instance of a tensor subclass requires "
                            "set_() to be implemented correctly for the tensor subclass."
                            "Alternatively, one can opt into the swap_tensors path"
                            "Either set leave_parametrized=False or provide a working implementation"
                            "for set_() in the tensor subclass or set "
                            "torch.__future__.set_swap_module_params_on_conversion(True)."
                        ) from e
    else:
        if leave_parametrized:
            # We cannot use no_grad because we need to know whether one or more
            # original tensors required grad
            t = getattr(module, tensor_name)
            # We'll have to trust the user to add it to the optimizer
            original = Parameter(t) if t.requires_grad else t
        else:
            raise ValueError(
                "Cannot leave unparametrized (`leave_parametrized=False`) a tensor "
                "that is parametrized in terms of a sequence of tensors."
            )

    # Delete the property that manages the parametrization
    delattr(module.__class__, tensor_name)
    # Delete the ParametrizationList
    del module.parametrizations[tensor_name]

    # Restore the parameter / buffer into the main class
    _register_parameter_or_buffer(module, tensor_name, original)

    # Roll back the parametrized class if no other buffer or parameter
    # is currently parametrized in this class
    if not is_parametrized(module):
        delattr(module, "parametrizations")
        # Restore class
        orig_cls = module.__class__.__bases__[0]
        module.__class__ = orig_cls
    return module