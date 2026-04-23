def convert_arg_type_and_name(
    typ: Type,
    name: str,
    is_write: bool = False,
) -> tuple[list[str], list[str], list[str], list[str]]:
    if isinstance(typ, BaseType):
        if typ.name in base_type_to_c_type:
            if typ.name == BaseTy.Tensor and is_write:
                # For output tensors, our normal call to resolve_tensor_dispatch_flags
                # results in an rvalue tensor, which can't be passed to at::Tensor&.
                # Override this case specifically.
                callsite_expr = [f"*tensor_handle_to_tensor_pointer({name})"]
            else:
                callsite_expr = [
                    f"{base_type_to_callsite_expr[typ.name]}({name})"
                    if base_type_to_callsite_expr[typ.name]
                    else name
                ]

            return (
                [base_type_to_c_type[typ.name]],
                [name],
                [base_type_to_aten_type[typ.name]],
                callsite_expr,
            )
        elif typ.name == BaseTy.Device:
            return (
                ["int32_t", "int32_t"],
                [name, name + "_index_"],
                ["c10::Device"],
                [
                    f"c10::Device(static_cast<c10::DeviceType>({name}), static_cast<c10::DeviceIndex>({name}_index_))"
                ],
            )
        else:
            # TODO: BaseTy.Dimname, etc.
            raise NotImplementedError(f"TODO: add support for arg type {repr(typ)}")
    elif isinstance(typ, OptionalType):
        c_types, names, aten_types, callsite_exprs = convert_arg_type_and_name(
            typ.elem, name
        )
        j = 0  # index for names
        new_aten_types = []
        new_callsite_exprs = []
        for aten_type in aten_types:
            # Use pointer to denote optional type
            c_types[j] = c_types[j] + "*"
            if aten_type.startswith("c10::ArrayRef<"):
                # ArrayRef is passed as pointer + size, but no need to add "*" to the size argument
                new_aten_types.append(f"::std::optional<{aten_type}>")
                base_type = aten_type[len("c10::ArrayRef<") : -1]
                new_callsite_exprs.append(
                    f"pointer_to_optional_list<{base_type}>({names[j]}, {names[j + 1]})"
                )
                j += 2
            elif aten_type == "c10::Device":
                # Device is passed as device_type + device_index
                new_aten_types.append("::std::optional<c10::Device>")
                new_callsite_exprs.append(
                    f"pointer_to_optional_device({names[j]}, {names[j + 1]})"
                )
                j += 2
            elif aten_type == "at::Tensor":
                new_aten_types.append(f"::std::optional<{aten_type}>")
                new_callsite_exprs.append(f"resolve_tensor_dispatch_flags({names[j]})")
                j += 1
            else:
                new_aten_types.append(f"::std::optional<{aten_type}>")
                new_callsite_exprs.append(
                    f"pointer_to_optional<{aten_type}>({names[j]})"
                )
                j += 1

        return (
            c_types,
            names,
            new_aten_types,
            new_callsite_exprs,
        )
    elif isinstance(typ, ListType):
        # Need to explicitly pass the list as pointer + length
        c_types, names, aten_types, _ = convert_arg_type_and_name(typ.elem, name)
        if len(c_types) != 1:
            raise AssertionError(f"ListType with unsupported element type {repr(typ)}")

        # The list content should never be modified
        c_types[0] = f"const {c_types[0]}*"
        c_types.append("int64_t")
        name = names[0]
        names.append(name + "_len_")

        atype = aten_types[0]
        callsite_exprs = []
        if atype == "bool":
            # no converter from std::vector<bool> to c10::ArrayRef<bool>
            # construct std::array<bool, N> instead
            if typ.size is None:
                raise AssertionError("bool ListType must have a size")
            callsite_exprs.append(f"pointer_to_list<{typ.size}>({name})")
        elif atype == "at::Tensor" and not is_write:
            callsite_exprs.append(
                f"resolve_tensor_list_dispatch_flags({name}, {name}_len_)"
            )
        elif atype == "::std::optional<at::Tensor>":
            # convert from std::vector<::std::optional<at::Tensor>> to c10::List<::std::optional<at::Tensor>>
            callsite_exprs.append(
                f"c10::List<{atype}>(c10::ArrayRef<{atype}>(resolve_tensor_list_dispatch_flags({name}, {name}_len_)))"
            )
        else:
            callsite_exprs.append(f"pointer_to_list<{atype}>({name}, {name}_len_)")

        aten_types = [f"c10::ArrayRef<{t}>" for t in aten_types]
        return (
            c_types,
            names,
            aten_types,
            callsite_exprs,
        )
    raise NotImplementedError(f"Argument type {repr(typ)} not supported!")