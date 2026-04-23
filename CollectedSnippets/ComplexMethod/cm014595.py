def gen(self, schema: LazyIrSchema) -> list[str]:
        opkind = schema.opkind or aten_symbol(schema)

        # for now, we just want one IR class decl and soon after also the method defs
        # and we use the functional version not out/inplace.
        all_args = schema.filtered_args()
        scalar_args = schema.filtered_args(values=False, scalars=True)

        ctor_args = [f"const {i.lazy_type.cpp_type()}& {i.name}" for i in all_args]
        reuse_ctor_args = ", ".join(ctor_args)
        if self.use_lazy_shape and schema.properties.ShapePrecompute:
            ctor_args.append("std::vector<torch::lazy::Shape>&& shapes")
        node_ctor_args = ", ".join(ctor_args)

        scalar_initializers = ",\n        ".join(
            [
                # This code is just special casing the mapping from string_view -> strings
                f"{a.name}({a.name}.has_value() ? ::std::make_optional(std::string(*{a.name})) : ::std::nullopt)"
                if a.lazy_type.cpp_type() == "::std::optional<c10::string_view>"
                else f"{a.name}({a.name})"
                for a in scalar_args
            ]
        )
        if len(scalar_initializers):
            scalar_initializers = f",\n        {scalar_initializers}"
        scalar_decls = "\n  ".join(
            [
                f"std::string {a.name};"
                if a.lazy_type.cpp_type() == "c10::string_view"
                else f"::std::optional<std::string> {a.name};"
                if a.lazy_type.cpp_type() == "::std::optional<c10::string_view>"
                else f"{a.lazy_type.cpp_type()} {a.name};"
                for a in scalar_args
            ]
        )
        optional_values = [
            arg.name
            for arg in schema.filtered_args(values=True, scalars=False)
            if isinstance(arg.lazy_type, OptionalCType)
        ]
        has_optional_decls = "\n  ".join(
            [f"bool has_{value}: 1;" for value in optional_values]
        )
        has_optional_defs = "\n    ".join(
            [f"has_{value} = !!{value};" for value in optional_values]
        )
        members_to_string = []
        for arg in scalar_args:
            if isinstance(arg.lazy_type, OptionalCType):
                value = f"{arg.name}.value()"
                if arg.is_generator:
                    value = '"torch.Generator()"'
                members_to_string.append(
                    f"""if ({arg.name}.has_value()) {{
      ss << ", {arg.name}=" << {value};
    }} else {{
      ss << ", {arg.name}=null";
    }}"""
                )
            else:
                members_to_string.append(f'ss << ", {arg.name}=" << {arg.name};')
        members_to_string_str = "\n    ".join(members_to_string)

        return [
            f"""\
class {schema.node_name} : public {self.node_base} {{
 public:
  static torch::lazy::OpKind ClassOpKind() {{
    return torch::lazy::OpKind({opkind});
  }}

  {schema.node_name}({node_ctor_args})
      : {self.node_base_ctor_call(schema)}{scalar_initializers}
  {{
    {has_optional_defs}
  }}

  std::string ToString() const override {{
    std::stringstream ss;
    ss << {self.node_base}::ToString();
    {members_to_string_str}
    return ss.str();
  }}

  {self.create_function(schema, reuse_ctor_args)}

  {self.can_be_reused_function(schema, reuse_ctor_args)}

  {self.lowering_function(schema)}

  {scalar_decls}
  {has_optional_decls}

}};

""",
        ]