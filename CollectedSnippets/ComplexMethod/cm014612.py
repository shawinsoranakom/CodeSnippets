def test_value_expression(
    arg_type: BaseType | OptionalType | Type, index: int, op_name: str
) -> str:
    tensor_size_ex = test_tensor_shape(op_name)
    if tensor_size_ex == "":
        num_tensors = 16 if index == 0 else 64
        num_dim = test_tensor_dim(op_name)
        size_per_dim = math.ceil(num_tensors / float(num_dim))
        size_per_dim += size_per_dim % 2
        tensor_size_ex = "{{{}}}".format(",".join([f"{size_per_dim}"] * num_dim))
    if should_use_int_tensor(op_name):
        tensor_expression = f"at::randint(1, 100, {tensor_size_ex}, at::kInt)"
    elif should_use_complex_tensor(op_name):
        tensor_expression = f"at::randn({tensor_size_ex}, at::kComplexFloat)"
    else:
        tensor_expression = f"at::rand({tensor_size_ex})"

    value_expressions = {
        BaseTy.Tensor: tensor_expression,
        BaseTy.int: "1",
        BaseTy.bool: "false",
        BaseTy.Scalar: "2",
        BaseTy.ScalarType: "at::ScalarType::Float",
        BaseTy.str: '"floor"',
    }

    base_ty_object = None
    if isinstance(arg_type, BaseType):
        base_ty_object = arg_type.name
    else:
        if not (
            isinstance(arg_type, OptionalType) and isinstance(arg_type.elem, BaseType)
        ):
            raise AssertionError(
                f"Expected OptionalType with BaseType elem, got {type(arg_type)}"
            )
        base_ty_object = arg_type.elem.name
    if base_ty_object not in value_expressions:
        raise AssertionError(f"Unexpected type: {base_ty_object}")
    value_expression = value_expressions[base_ty_object]
    return value_expression