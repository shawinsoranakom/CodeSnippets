def transfer_parametrizations_and_params(
    from_module: Module,
    to_module: Module,
    tensor_name: str | None = None,
) -> Module:
    r"""Transfer parametrizations and the parameters they parametrize from :attr:`from_module` to :attr:`to_module`.

    If :attr:`tensor_name` is specified, only transfers the specified parameter, otherwise
    transfers all parametrized parameters. If those parameters do not exist in to_module, it will create them.
    Does nothing if from_module is not parametrized.

    Args:
        from_module (nn.Module): module to transfer from
        to_module (nn.Module): module to transfer to
        tensor_name (str, optional): parameter to transfer

    Returns:
        Module: to_module
    """
    if is_parametrized(from_module):
        if not isinstance(from_module.parametrizations, ModuleDict):
            raise AssertionError(
                f"Expected from_module.parametrizations to be a ModuleDict, "
                f"got {type(from_module.parametrizations).__name__}"
            )

        # get list of all params or the single param to transfer
        parameters_to_transfer: list | ModuleDict = (
            from_module.parametrizations if tensor_name is None else [tensor_name]
        )

        if not hasattr(parameters_to_transfer, "__iter__"):
            raise AssertionError(
                f"Expected parameters_to_transfer to be iterable, "
                f"got {type(parameters_to_transfer).__name__}"
            )
        for parameter_name in parameters_to_transfer:
            # initialize the to-be-transferred param in to_module if it doesn't exist already
            if not hasattr(to_module, parameter_name):
                setattr(
                    to_module,
                    parameter_name,
                    Parameter(getattr(from_module, parameter_name)),
                )

            # apply the params's parametrizations to to_module
            for param_func in from_module.parametrizations[  # type: ignore[attr-defined]
                parameter_name
            ]:
                register_parametrization(to_module, parameter_name, param_func)
            if not isinstance(to_module.parametrizations, ModuleDict):
                raise AssertionError(
                    f"Expected to_module.parametrizations to be a ModuleDict, "
                    f"got {type(to_module.parametrizations).__name__}"
                )

            # make values match, original values can be stored in either original or
            # original0, original1..., need to check both cases
            if hasattr(from_module.parametrizations[parameter_name], "original"):
                to_module.parametrizations[
                    parameter_name
                ].original = from_module.parametrizations[parameter_name].original
            else:
                num = 0
                orig_num = "original" + str(num)
                # loop through each original# until all values have been set
                while hasattr(from_module.parametrizations[parameter_name], orig_num):
                    setattr(
                        to_module.parametrizations[parameter_name],
                        orig_num,
                        getattr(from_module.parametrizations[parameter_name], orig_num),
                    )
                    num = num + 1
                    orig_num = "original" + str(num)

    return to_module