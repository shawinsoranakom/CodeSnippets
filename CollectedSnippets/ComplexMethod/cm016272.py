def save_var(var: SavedAttribute, is_output: bool) -> None:
        name = var.nctype.name
        type = var.nctype.type
        should_append_getsetdef = True
        should_append_raw_getsetdef = False
        visit_name = name
        uses_cpp_saved_variable_cls = False
        unpacked_ref_type = None

        if (
            type == BaseCType(tensorT)
            or type == OptionalCType(BaseCType(tensorT))
            or type == MutRefCType(OptionalCType(BaseCType(tensorT)))
            or (type == BaseCType(scalarT) and is_output)
        ):
            uses_cpp_saved_variable_cls = True
            saved_variables.append(f"SavedVariable {name}_;")
            release_variables.append(f"{name}_.reset_data();")
            ptr = "shared_from_this()" if is_output else ""
            unpack.append(f"auto {name} = {name}_.unpack({ptr});")
            getter_definitions.append(
                GETTER_DEFINITION_SAVEDVAR.substitute(
                    op=info.op, name=name, body=GETTER_BODY_SAVEDVAR
                )
            )
            getter_definitions.append(
                GETTER_DEFINITION_RAW_SAVEDVAR.substitute(
                    op=info.op, name=name, body=GETTER_BODY_RAW_SAVEDVAR
                )
            )
            should_append_raw_getsetdef = True
            visit_name = f"{name}_"
            unpacked_ref_type = "Tensor&"
        elif (
            type == BaseCType(tensorListT)
            or type == BaseCType(iTensorListRefT)
            or type == VectorCType(BaseCType(tensorT))
        ):
            # note(crcrpar): [nuanced return type of out-of-place foreach functions]
            # When an out-of-place foreach function whose return signature is `Tensor[]`
            # spells out its backward definitions in `derivatives.yaml`, and some of them depend on
            # `result`, `result`'s type is interpreted and treated as `std::vector<Tensor>`.
            # An out-of-place foreach whose backwards rely on their output doesn't suffer from this
            # difference if the definitions are codegen'ed.
            # This special case is needed for `_foreach_pow.List` and `_foreach_pow.ScalarAndTensor`
            # as of https://github.com/pytorch/pytorch/pull/105504.
            if type == VectorCType(BaseCType(tensorT)):
                if not (
                    info.func.func.name.name.base.startswith("_foreach") and is_output
                ):
                    raise AssertionError(
                        "VectorCType(BaseCType(tensorT)) requires foreach function and is_output"
                    )
            uses_cpp_saved_variable_cls = True
            saved_variables.append(f"std::vector<SavedVariable> {name}_;")
            saved_variables.append(f"bool {name}_released_ = false;")
            # Just clear() is sufficient, we don't need to loop and clear each variable.
            # Because the SavedVariable owns a tensor and a grad_fn, removing the SavedVariable makes them go away as well.
            release_variables.append(f"{name}_.clear();")
            release_variables.append(f"{name}_released_ = true;")
            ptr = "shared_from_this()" if is_output else "nullptr"
            unpack.append(f"auto {name} = unpack_list({name}_, {ptr});")
            asserts.append(f"TORCH_CHECK(!{name}_released_, ERR_BACKWARD_TWICE);")
            getter_definitions.append(
                GETTER_DEFINITION_VEC_SAVEDVAR.substitute(
                    op=info.op, name=name, body=GETTER_BODY_VEC_SAVEDVAR
                )
            )
            getter_definitions.append(
                GETTER_DEFINITION_RAW_VEC_SAVEDVAR.substitute(
                    op=info.op, name=name, body=GETTER_BODY_RAW_VEC_SAVEDVAR
                )
            )
            should_append_raw_getsetdef = True
            visit_name = f"{name}_"
            unpacked_ref_type = "std::vector<Tensor>&"
        elif type == ListCType(OptionalCType(BaseCType(tensorT))):
            uses_cpp_saved_variable_cls = True
            saved_variables.append(f"std::vector<SavedVariable> {name}_;")
            saved_variables.append(f"bool {name}_released_ = false;")
            # Just clear() is sufficient, we don't need to loop and clear each variable.
            # Because the SavedVariable owns a tensor and a grad_fn, removing the SavedVariable makes them go away as well.
            release_variables.append(f"{name}_.clear();")
            release_variables.append(f"{name}_released_ = true;")
            unpack.append(f"auto {name} = unpack_opt_list({name}_);")
            asserts.append(f"TORCH_CHECK(!{name}_released_, ERR_BACKWARD_TWICE);")
            getter_definitions.append(
                GETTER_DEFINITION_VEC_SAVEDVAR.substitute(
                    op=info.op, name=name, body=GETTER_BODY_VEC_SAVEDVAR
                )
            )
            getter_definitions.append(
                GETTER_DEFINITION_RAW_VEC_SAVEDVAR.substitute(
                    op=info.op, name=name, body=GETTER_BODY_RAW_VEC_SAVEDVAR
                )
            )
            should_append_raw_getsetdef = True
            visit_name = f"{name}_"
            unpacked_ref_type = "torch::List<std::optional<Tensor>>&"
        elif type == BaseCType(intArrayRefT):
            saved_variables.append(f"std::vector<int64_t> {name};")
            getter_definitions.append(
                GETTER_DEFINITION.substitute(
                    op=info.op, name=name, body=GETTER_BODY_ARRAYREF_LONG
                )
            )
        elif type == BaseCType(symIntArrayRefT):
            saved_variables.append(f"std::vector<c10::SymInt> {name};")
            getter_definitions.append(
                GETTER_DEFINITION.substitute(
                    op=info.op, name=name, body=GETTER_BODY_ARRAYREF_SYMINT
                )
            )
        elif type == BaseCType(optionalIntArrayRefT):
            saved_variables.append(f"c10::OptionalArray<int64_t> {name};")
            getter_definitions.append(
                GETTER_DEFINITION_OPT_ARRAYREF.substitute(
                    op=info.op, name=name, body=GETTER_BODY_ARRAYREF_LONG
                )
            )
        elif type == BaseCType(optionalSymIntArrayRefT):
            saved_variables.append(f"c10::OptionalArray<c10::SymInt> {name};")
            getter_definitions.append(
                GETTER_DEFINITION_OPT_ARRAYREF.substitute(
                    op=info.op, name=name, body=GETTER_BODY_ARRAYREF_SYMINT
                )
            )
        elif type == OptionalCType(BaseCType(intArrayRefT)):
            saved_variables.append(f"c10::OptionalArray<int64_t> {name};")
            getter_definitions.append(
                GETTER_DEFINITION_OPT_ARRAYREF.substitute(
                    op=info.op, name=name, body=GETTER_BODY_ARRAYREF_LONG
                )
            )
        elif type == OptionalCType(BaseCType(symIntArrayRefT)):
            saved_variables.append(f"c10::OptionalArray<c10::SymInt> {name};")
            getter_definitions.append(
                GETTER_DEFINITION_OPT_ARRAYREF.substitute(
                    op=info.op, name=name, body=GETTER_BODY_ARRAYREF_SYMINT
                )
            )
        elif type == OptionalCType(ArrayRefCType(BaseCType(doubleT))):
            saved_variables.append(f"c10::OptionalArray<double> {name};")
            getter_definitions.append(
                GETTER_DEFINITION_OPT_ARRAYREF.substitute(
                    op=info.op, name=name, body=GETTER_BODY_ARRAYREF_DOUBLE
                )
            )
        elif type == BaseCType(longT):
            saved_variables.append(f"{type.cpp_type()} {name} = 0;")
            getter_definitions.append(
                GETTER_DEFINITION.substitute(
                    op=info.op, name=name, body=GETTER_BODY_INT64_T
                )
            )
        elif type == BaseCType(SymIntT):
            saved_variables.append(f"c10::SymInt {name};")
            getter_definitions.append(
                GETTER_DEFINITION.substitute(
                    op=info.op, name=name, body=GETTER_BODY_SYMINT
                )
            )
        elif type == BaseCType(stringT):
            saved_variables.append(f"std::string {name};")
            getter_definitions.append(
                GETTER_DEFINITION.substitute(
                    op=info.op, name=name, body=GETTER_BODY_STRING
                )
            )
        elif type == OptionalCType(BaseCType(stringT)):
            saved_variables.append(f"std::optional<std::string> {name};")
            getter_definitions.append(
                GETTER_DEFINITION_OPT.substitute(
                    op=info.op, name=name, body=GETTER_BODY_STRING
                )
            )
        elif type == ArrayRefCType(
            elem=BaseCType(type=BaseCppType(ns="at", name="Scalar"))
        ):
            saved_variables.append(f"std::vector<at::Scalar> {name};")
            unpacked_ref_type = "std::vector<at::Scalar>&"
            saved_variables.append(f"bool {name}_released_ = false;")
            # Just clear() is sufficient, we don't need to loop and clear each variable.
            # Because the SavedVariable owns a tensor and a grad_fn, removing the SavedVariable makes them go away as well.
            release_variables.append(f"{name}.clear();")
            # release_variables.append(f"{name}_released_ = true;")
            # unpack.append(f"auto {name} = unpack_list({name}_);")
            # asserts.append(f"TORCH_CHECK(!{name}_released_, ERR_BACKWARD_TWICE);")
            getter_definitions.append(
                CodeTemplate(
                    """\
static PyObject* THP${op}_${name}_getter(THPCppFunction *self, void *_unused) {
  HANDLE_TH_ERRORS
  const auto *node = static_cast<${op}*>(self->cdata.get());
  const auto& prop = node->${name};
  if (node->${name}_released_) {
    PyErr_SetString(PyExc_RuntimeError, ERR_BACKWARD_TWICE);
    return nullptr;
  }
  ${body}
  END_HANDLE_TH_ERRORS
}
                            """
                ).substitute(
                    op=info.op,
                    name=name,
                    body=GETTER_BODY_VEC_SCALAR,
                )
            )
        else:
            # Check for indicators that you're putting a non-owning reference
            # into the saved variable field.  If this is spuriously firing,
            # edit this field.  Otherwise, you probably need to add a case
            # above.
            if not (
                "ref" not in type.cpp_type().lower()
                and "view" not in type.cpp_type().lower()
                and "*" not in type.cpp_type()
                and "&" not in type.cpp_type()
            ):
                raise AssertionError(
                    f"{type.cpp_type()} looks like it contains a non-owning reference"
                )
            saved_variables.append(f"{type.cpp_type()} {name};")

            if type in MISC_GETTER_DEFS:
                getter_def, body = MISC_GETTER_DEFS[type]
                getter_definitions.append(
                    getter_def.substitute(op=info.op, name=name, body=body)
                )
            else:
                # Types we don't expose python bindings to yet:
                #   TypeAndSize, at::ScalarType, TensorOptions, TensorGeometry,
                #   std::vector<std::vector<int64_t>>, std::vector<at::ScalarType>
                should_append_getsetdef = False

        if should_append_getsetdef:
            py_getsetdef_structs.append(
                PY_GETSETDEF_STRUCT.substitute(op=info.op, name=name)
            )
        if should_append_raw_getsetdef:
            py_getsetdef_structs.append(
                PY_RAW_GETSETDEF_STRUCT.substitute(op=info.op, name=name)
            )

        if uses_cpp_saved_variable_cls:
            compiled_args.append(
                f"args.collect({visit_name}, {'true' if is_output else 'false'});"
            )
        else:
            compiled_args.append(f"args.collect({visit_name});")
        apply_with_saved_before.append(f"saved.before({visit_name});")
        apply_with_saved_after.append(f"saved.after({visit_name});")

        if unpacked_ref_type is None:
            unpacked_ref_type = f"{saved_variables[-1].split(' ')[0]}&"
        apply_functional_args.append(str(name))
        apply_functional_args_ref_types.append(unpacked_ref_type)