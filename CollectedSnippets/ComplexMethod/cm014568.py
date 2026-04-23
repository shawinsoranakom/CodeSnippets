def decl(self) -> list[str]:
        base_ctor_arguments = functionalization.base_ctor_arguments(self.f.func)
        extra_ctor_arguments = functionalization.extra_ctor_arguments(self.f.func)
        attributes = functionalization.attributes(self.f.func)

        # List of types for declaring the `SerializableTuple` type.
        serializable_tuple_args = ",\n".join(
            f"      {binding.type} /* {binding.name} */"
            for binding in (base_ctor_arguments + attributes)
        )

        # Arguments used for forwarding the tuple elements to the constructor.
        destructure_tuple_args = ", ".join(
            f"std::get<{i}>(tpl)"
            for i in range(len(base_ctor_arguments) + len(extra_ctor_arguments))
        )

        # List of constructor parameters
        ctor_parameters = ", ".join(
            binding.decl() for binding in (base_ctor_arguments + extra_ctor_arguments)
        )

        # Call the base class `ViewMeta` constructor.
        #
        # Both of `is_multi_output` and `is_as_strided` are known values, given the
        # operation schema.
        is_multi_output_str = str(self.is_multi_output).lower()
        is_as_strided_str = str(self.is_as_strided).lower()

        base_ctor_bindings = ", ".join(
            [
                # `has_symbolic_inputs` is always taken as parameter.
                functionalization.has_symbolic_inputs_binding.name,
                f"/*is_multi_output=*/{is_multi_output_str}",
                f"/*is_as_strided=*/{is_as_strided_str}",
                # `out_index` is know if the operation returns only one value. Otherwise,
                # we also take it as parameter.
                f"/*out_index=*/{self.out_index}",
            ]
        )

        # Assignments of `extra_ctor_arguments` to their corresponding fields.
        # These are extra fields to-be-declared in this specialization.
        #
        # We need to set `allow_expensive_conversions`, since we are storing owned versions
        # of the non-owning arguments.
        ctor_assignments = ",\n".join(
            f"        {e.type.name}({e.expr})"
            for e in translate(
                extra_ctor_arguments,
                attributes,
                method=False,
                allow_expensive_conversions=True,
            )
        )

        # List of arguments for constructing the `SerializableTuple` from an instance.
        tuple_arguments = ", ".join(
            binding.name for binding in (base_ctor_arguments + attributes)
        )

        # List of field declarations.
        attr_declarations = "\n".join(f"  {binding.decl()};" for binding in attributes)

        # Override `to_out_index` if this operation returns more than 1 value.
        to_out_index_decl = ""
        if self.is_multi_output:
            to_out_index_decl = (
                "  std::shared_ptr<ViewMeta> to_out_index(int64_t out_idx) override;"
            )

        return [
            f"""
struct TORCH_API {self.classname} : public ViewMeta {{
  FUNCTIONALIZATION_VIEWMETA_NAME({self.classname})
  FUNCTIONALIZATION_VIEWMETA_SERIALIZABLE_TUPLE(\n{serializable_tuple_args});

  {self.classname}(const SerializableTuple& tpl)
      : {self.classname}({destructure_tuple_args}) {{}}

  {self.classname}({ctor_parameters})
      : at::functionalization::ViewMeta({base_ctor_bindings}),
{ctor_assignments} {{}}

  Tensor forward(const Tensor& base) override;
  Tensor reverse(const Tensor& base, const Tensor& mutated_view) override;
{to_out_index_decl}

  SerializableTuple to_serializable_tuple() {{
    return std::make_tuple({tuple_arguments});
  }}

{attr_declarations}
}};
"""
        ]