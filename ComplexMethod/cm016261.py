def saved_variables(
    formula: str,
    nctypes: list[NamedCType],
    var_names: tuple[str, ...],
) -> tuple[str, tuple[SavedAttribute, ...]]:
    def stride_expr(name: str) -> str:
        if var_names != (name,):
            raise AssertionError(
                'Replacement for ".strides()" is currently only supported for single derivatives of the same tensor '
                'that ".strides()" is being called on.'
            )
        return f'strides_or_error({name}, "{name}")'

    REPLACEMENTS: list[tuple[str, dict[str, Any]]] = [
        # replace self.sym_sizes() with self_sym_sizes
        (
            r"{}.sym_sizes\(\)",
            {
                "suffix": "_sym_sizes",
                "nctype": lambda name: NamedCType(name, BaseCType(symIntArrayRefT)),
            },
        ),
        # replace self->sym_sizes() with self_sym_sizes_opt
        (
            r"{}->sym_sizes\(\)",
            {
                "suffix": "_sym_sizes_opt",
                "nctype": lambda name: NamedCType(
                    name, OptionalCType(BaseCType(symIntArrayRefT))
                ),
                "expr": lambda name: f"{name}.has_value() ? std::optional<c10::SymIntArrayRef>({name}->sym_sizes()) : std::nullopt",
            },
        ),
        # replace self.sym_blocksize() with self_sym_blocksize_opt
        (
            r"{}.sym_blocksize\(\)",
            {
                "suffix": "_self_sym_blocksize_opt",
                "nctype": lambda name: NamedCType(
                    name, OptionalCType(BaseCType(symIntArrayRefT))
                ),
                "expr": lambda name: f"at::sparse_csr::getSymIntBlockSize({name})",
            },
        ),
        # replace self.options() with self_options
        (
            r"{}.options\(\)",
            {
                "suffix": "_options",
                "nctype": lambda name: NamedCType(name, BaseCType(tensorOptionsT)),
            },
        ),
        # replace zeros_like(self) with self_info
        (
            r"zeros_like\({}\)",
            {
                "suffix": "_info",
                "nctype": lambda name: NamedCType(name, BaseCType(typeAndSizeT)),
                "expr": lambda name: name,  # at save-time
                "res": lambda name: name + "_info.zeros()",  # at eval-time
            },
        ),
        # replace self.sym_size(2) with self_sym_size_2
        (
            r"{}.sym_size\((-?\w+)\)",
            {
                "suffix": lambda m: f"_sym_argsize_{m.groups()[0].replace('-', 'minus_')}",
                "nctype": lambda name: NamedCType(name, BaseCType(SymIntT)),
            },
        ),
        # replace self.numel() with self_numel
        (
            r"{}.numel\(\)",
            {
                "suffix": "_numel",
                "nctype": lambda name: NamedCType(name, BaseCType(longT)),
            },
        ),
        # replace self.sym_numel() with self_sym_numel
        (
            r"{}.sym_numel\(\)",
            {
                "suffix": "_sym_numel",
                "nctype": lambda name: NamedCType(name, BaseCType(SymIntT)),
            },
        ),
        # replace to_args_sizes(self) with self_args_sizes
        (
            r"to_args_sizes\({}\)",
            {
                "suffix": "_args_sizes",
                "nctype": lambda name: NamedCType(
                    name, VectorCType(VectorCType(BaseCType(longT)))
                ),
            },
        ),
        # replace to_args_sizes_symint(self) with self_args_sizes
        (
            r"to_args_sizes_symint\({}\)",
            {
                "suffix": "_args_sizes_symint",
                "nctype": lambda name: NamedCType(
                    name, VectorCType(VectorCType(BaseCType(SymIntT)))
                ),
            },
        ),
        # replace to_args_scalartypes(self) with self_args_scalartypes
        (
            r"to_args_scalartypes\({}\)",
            {
                "suffix": "_args_scalartypes",
                "nctype": lambda name: NamedCType(
                    name, VectorCType(BaseCType(scalarTypeT))
                ),
            },
        ),
        # replace TensorGeometry(self) with self_geometry
        (
            r"TensorGeometry\({}\)",
            {
                "suffix": "_geometry",
                "nctype": lambda name: NamedCType(name, BaseCType(tensorGeometryT)),
            },
        ),
        (
            r"{}.scalar_type\(\)",
            {
                "suffix": "_scalar_type",
                "nctype": lambda name: NamedCType(name, BaseCType(scalarTypeT)),
            },
        ),
        # replace self.dim() with self_dim
        (
            r"{}.dim\(\)",
            {
                "suffix": "_dim",
                "nctype": lambda name: NamedCType(name, BaseCType(longT)),
            },
        ),
        # replace self.sym_strides() with self_sym_strides
        (
            r"{}.sym_strides\(\)",
            {
                "suffix": "_sym_strides",
                "nctype": lambda name: NamedCType(name, BaseCType(symIntArrayRefT)),
                "expr": stride_expr,
            },
        ),
        # replace self.layout() with self_layout
        (
            r"{}.layout\(\)",
            {
                "suffix": "_layout",
                "nctype": lambda name: NamedCType(name, BaseCType(layoutT)),
            },
        ),
        # replace self.is_conj() with self_conjugate
        (
            r"{}.is_conj\(\)",
            {
                "suffix": "_conjugate",
                "nctype": lambda name: NamedCType(name, BaseCType(boolT)),
            },
        ),
    ]

    # find which arguments need to be saved
    saved: list[SavedAttribute] = []

    if ".sizes()" in formula or "->sizes()" in formula:
        raise RuntimeError(
            ".sizes() is not supported in derivative formulas. Instead, please use the SymInt version,"
            + f".sym_sizes(), which returned a c10::SymIntArrayRef. formula={formula}"
        )
    if re.search(r"\.size\([-]?\d+\)", formula) or re.search(
        r"->size\([-]?\d+\)", formula
    ):
        raise RuntimeError(
            ".size(int) is not supported in derivative formulas. Instead, please use the SymInt version,"
            + f".sym_size(int), which returned a c10::SymIntArrayRef. formula={formula}"
        )
    if ".strides()" in formula or "->strides()" in formula:
        raise RuntimeError(
            ".strides() is not supported in derivative formulas. Instead, please use the SymInt version,"
            + f".sym_strides(), which returned a c10::SymIntArrayRef. formula={formula}"
        )
    for nctype in nctypes:
        name = (
            nctype.name.name if isinstance(nctype.name, SpecialArgName) else nctype.name
        )
        # First search the formula for expressions which can be evaluated
        # when the autograd Function is created to avoid saving variables
        for regex, info in REPLACEMENTS:

            def repl(m: re.Match[str]) -> str:
                suffix: str = (
                    # pyrefly: ignore [bad-assignment]
                    info["suffix"](m) if callable(info["suffix"]) else info["suffix"]
                )
                expr: str = info["expr"](name) if "expr" in info else m.group(0)
                saved.append(
                    SavedAttribute(
                        nctype=info["nctype"](name + suffix),
                        expr=expr,
                    )
                )
                if "res" in info:
                    replacement: str = info["res"](name)
                    return replacement
                return name + suffix

            formula = re.sub(regex.format(name), repl, formula)

        # std::optional<std::string> types stored in Backward nodes must be
        # converted to std::optional<std::string_view> before being passed into
        # the backward function
        if nctype.type == OptionalCType(BaseCType(stringT)):
            formula = re.sub(
                rf"\b{name}\b",
                f"{name}.has_value() ? std::optional<std::string_view>({name}.value()) : std::nullopt",
                formula,
            )

        # Find any variables which remain in the formula and save them
        if re.search(IDENT_REGEX.format(name), formula):
            saved.append(
                SavedAttribute(
                    nctype=nctype,
                    expr=name,
                )
            )

    return formula, tuple(saved)