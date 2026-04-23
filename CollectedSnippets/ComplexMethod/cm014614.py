def out_variant_op_test_case_generator(self, g: NativeFunctionsGroup) -> str:
        schema = g.functional.func
        schema_str = str(schema)
        if schema_str.find("(") <= 0:
            raise AssertionError(f"Invalid schema string: {schema_str}")
        type_variant_op_name = schema_str[: schema_str.find("(")].replace(".", "_")
        op_name = op_name_from_group(g)
        if not type_variant_op_name.startswith(op_name):
            raise AssertionError(
                f"Type variant op name {type_variant_op_name} doesn't start with {op_name}"
            )

        arg_types = generate_test_ir_arguments(schema)
        arg_declarations = ", ".join(
            (
                arg_name if arg_type is None else f"{arg_name}: {arg_type}"
                for arg_name, arg_type in arg_types
            )
        )
        arg_names = ", ".join((arg_name for arg_name, _ in arg_types))
        if not (
            len(schema.returns) == 1
            and isinstance(schema.returns[0].type, BaseType)
            and schema.returns[0].type.name is BaseTy.Tensor
        ):
            raise AssertionError(f"Expected single Tensor return, got {schema.returns}")
        test_value_definitions = generate_test_value_definitions(schema, 0)
        test_value_names = generate_test_value_names(schema, 0)
        test_value_definitions2 = generate_test_value_definitions(schema, 1)
        test_value_names2 = generate_test_value_names(schema, 1)
        check_resize = "true" if should_check_resize(schema) else "false"
        generated = f"""
TEST(StaticRuntime, autogen_{type_variant_op_name}) {{
  const std::string script = R"IR(
    graph({arg_declarations}):
        %bias: None = prim::Constant()
        %ret = aten::{op_name}({arg_names})
        %cloned = aten::clone(%ret, %bias)
        return (%cloned)
  )IR";

  {test_value_definitions}
  std::vector<IValue> args{{{test_value_names}}};
  testStaticRuntime(script, args, {{}}, /*use_allclose=*/false, /*use_equalnan=*/false, /*check_resize=*/{check_resize});

  {test_value_definitions2}
  std::vector<IValue> args2{{{test_value_names2}}};
  testStaticRuntime(script, args, args2, /*use_allclose=*/false, /*use_equalnan=*/false, /*check_resize=*/{check_resize});

}}
"""
        return generated