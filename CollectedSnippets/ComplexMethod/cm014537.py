def compute_meta_function_declaration(g: NativeFunctionsGroup) -> str | None:
    if not g.structured:
        return None
    with native_function_manager(g.out):
        name = meta.name(g)
        args = structured.meta_arguments(g)
        args_str = ", ".join(a.decl() for a in args)
        parent_class = g.out.structured_inherits
        if parent_class is None:
            parent_class = "at::impl::MetaBase"
        meta_return = "void"
        precomputed = g.out.precomputed if g.structured else None

        if precomputed:
            # Generate the template declaration with one bool parameter for each
            # precomputed element. Each parameter is true if the corresponding (in
            # terms of position) precomputed element has been set.
            precomputed_values = [*precomputed.replace.values(), precomputed.add]
            precomputed_elements = [
                elem for replace_list in precomputed_values for elem in replace_list
            ]
            precomputed_template_parameters = [
                elem.name.upper() for elem in precomputed_elements
            ]
            precomputed_template_params_str = ", ".join(
                f"bool {param} = false" for param in precomputed_template_parameters
            )
            precompute_template_decl = f"template <{precomputed_template_params_str}>"

            # Generate a string containing declarations of all precomputed elements.
            precomputed_elements_with_cpp_types = [
                structured.argument_type(elem, binds=elem.name)
                for elem in precomputed_elements
            ]

            precomputed_elements_decl = ";\n".join(
                f"{elem.cpp_type(strip_ref=True)} {elem.name}"
                for elem in precomputed_elements_with_cpp_types
            )

            # Generate "setter" methods for each precomputed element. Each method will return
            # a new instance of precompute_out with the template parameter that corresponds to
            # the member set by the method to true (to indicate that it has been set).
            setter_methods = []
            for i, elem in enumerate(precomputed_elements):
                # Generate the signature. The return type will be the same
                # as the type of `this` but with the template parameter
                # corresponding to the element set by this method set to true.
                # The assert generated below will ensure that this template
                # parameter is false on the type of `this`.
                return_ty_templates = ", ".join(
                    precomputed_template_parameters[:i]
                    + ["true"]
                    + precomputed_template_parameters[i + 1 :]
                )
                return_ty = f"precompute_out<{return_ty_templates}>"
                elem_cpp_ty = precomputed_elements_with_cpp_types[i].cpp_type(
                    strip_ref=True
                )
                signature = f"{return_ty} set_{elem.name}({elem_cpp_ty} value)"

                # Generate an assert which checks that the
                # template parameter corresponding to the precomputed
                # element that is set by this method is false on the
                # class corresponding to the object that `this` points to.
                # This ensures that each element can be set only once.
                assert_msg = f'"{elem.name} already set"'
                assert_stmt = f"static_assert({precomputed_template_parameters[i]} == false, {assert_msg});"

                # Generate the new object construction block. All state
                # except the element that this method sets is copied from the
                # object that `this` points to. The value for the element that
                # the method sets is taken from a method parameter.
                construction_stmts = []
                construction_stmts.append(f"{return_ty} ret;")

                for j, elem in enumerate(precomputed_elements):
                    if i == j:
                        construction_stmts.append(f"ret.{elem.name} = value;")
                    else:
                        construction_stmts.append(
                            f"ret.{elem.name} = this->{elem.name};"
                        )

                construction_stmts.append("return ret;")
                construction_block = "\n".join(construction_stmts)

                setter_methods.append(
                    f"""
                    {signature} {{
                        {assert_stmt}
                        {construction_block}
                    }}
                """
                )
            setter_methods_decl = "\n".join(setter_methods)

            # Meta should return an instance of the struct containing the precomputed elements.
            meta_return_template_params = ", ".join(
                ["true"] * len(precomputed_template_parameters)
            )
            # This typedef (actually a using statement) is needed so that TORCH_META_FUNC can reuse the return
            # type (which has a variable number of template parameters).
            meta_return_typedef = f"using meta_return_ty = precompute_out <{meta_return_template_params}>;"
            meta_return = "meta_return_ty"
            precomputed_decl = f"""
                {precompute_template_decl}
                struct TORCH_API precompute_out {{
                    {setter_methods_decl}
                    {precomputed_elements_decl};
            }};"""
        else:
            meta_return_typedef = ""
            precomputed_decl = ""

        return f"""\
struct TORCH_API structured_{name} : public {parent_class} {{
    {precomputed_decl}
    {meta_return_typedef}
    {meta_return} meta({args_str});
}};
"""