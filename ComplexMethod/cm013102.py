def op_signature_from_function(
    func,
    domain: str,
    name: str | None = None,
    overload: str = "",
    *,
    since_version: int = 1,
) -> ir.schemas.OpSignature:
    """Produce an OpSignature from a function using type annotation."""

    py_signature = inspect.signature(func)
    # Not using inspect.get_annotations because typing.get_type_hints seems to handle more cases
    # https://github.com/python/cpython/issues/102405
    type_hints = typing.get_type_hints(func)

    params: list[ir.schemas.Parameter | ir.schemas.AttributeParameter] = []
    # Create a mapping from type to a unique name
    type_constraints: dict[str, ir.schemas.TypeConstraintParam] = {}

    for param in py_signature.parameters.values():
        if param.name not in type_hints:
            logger.debug(
                "Missing annotation for parameter '%s' from %s. Treating as an Input.",
                param.name,
                py_signature,
            )
            type_constraint = ir.schemas.TypeConstraintParam.any_value(
                f"T_{param.name}"
            )
            type_constraints[param.name] = type_constraint
            kwargs: dict[str, Any] = {}
            if param.default is not inspect.Parameter.empty:
                kwargs["default"] = param.default
            params.append(
                ir.schemas.Parameter(
                    name=param.name,
                    type_constraint=type_constraint,
                    required=param.default is inspect.Parameter.empty,
                    # TODO: Handle variadic
                    variadic=False,
                    **kwargs,
                )
            )
        else:
            type_ = type_hints[param.name]
            if (attr_type := _get_attr_type(type_)) != ir.AttributeType.UNDEFINED:
                # Construct the default attribute
                if param.default is not inspect.Parameter.empty:
                    # TODO: Use ir_convenience instead to handle int as float
                    default = ir.Attr(param.name, attr_type, param.default)
                else:
                    default = None
                params.append(
                    ir.schemas.AttributeParameter(
                        name=param.name,
                        type=attr_type,
                        required=param.default is inspect.Parameter.empty,
                        default=default,
                    )
                )
            else:
                # Obtain the type constraint from the type annotation

                # 1. Get a type constraint name from the type annotation
                # If the type annotation is a TypeVar or Optional[TypeVar], get its name
                # Otherwise, name it T_{param.name}
                type_constraint_name = _get_type_constraint_name(type_)
                if type_constraint_name is None:
                    type_constraint_name = f"T_{param.name}"

                # 2. If the type constraint param is already initialized, use it
                if type_constraint_name in type_constraints:
                    type_constraint = type_constraints[type_constraint_name]
                else:
                    # 3. Otherwise, create a new TypeConstraintParam
                    type_constraint = ir.schemas.TypeConstraintParam(
                        name=type_constraint_name,
                        allowed_types=_get_allowed_types_from_type_annotation(type_),
                    )
                    type_constraints[type_constraint_name] = type_constraint
                # 4. Create Parameter
                kwargs: dict[str, Any] = {}
                if param.default is not inspect.Parameter.empty:
                    kwargs["default"] = param.default
                params.append(
                    ir.schemas.Parameter(
                        name=param.name,
                        type_constraint=type_constraint,
                        required=param.default is inspect.Parameter.empty,
                        # TODO: Handle variadic
                        variadic=False,
                        **kwargs,
                    )
                )

    return_type = type_hints.get("return")

    outputs = []
    if return_type is None:
        # No returns
        pass
    else:
        if typing.get_origin(return_type) is tuple:
            # Multiple returns
            return_types = typing.get_args(return_type)
        else:
            return_types = [return_type]  # type: ignore[assignment]

        for i, return_type_i in enumerate(return_types):
            if (
                return_param_name := _get_type_constraint_name(return_type_i)
            ) in type_constraints:
                # pyrefly: ignore [bad-index]
                type_constraint = type_constraints[return_param_name]
            else:
                return_param_name = f"TReturn{i}"
                type_constraint = ir.schemas.TypeConstraintParam(
                    name=return_param_name,
                    allowed_types=_get_allowed_types_from_type_annotation(
                        return_type_i
                    ),
                )
                type_constraints[return_param_name] = type_constraint
            outputs.append(
                ir.schemas.Parameter(
                    name=return_param_name,
                    type_constraint=type_constraint,
                    required=True,
                    variadic=False,
                )
            )

    return ir.schemas.OpSignature(
        domain=domain,
        name=name or func.__name__,
        overload=overload,
        params=params,
        outputs=outputs,
        since_version=since_version,
    )