def argument_str_pyi(
        self, *, method: bool = False, deprecated: bool = False
    ) -> str:
        type_str = argument_type_str_pyi(self.type)

        name = self.name
        # s/self/input/ outside method bindings
        # [old codegen] TODO: remove this? doesn't rename in codegen, it's just
        # for the parse string
        if name == "self" and type_str == "Tensor" and not method and not deprecated:
            name = "input"

        if name == "from":  # from is a Python keyword...
            name += "_"

        # pyi merges the _out and functional variants into the same signature, with an optional out arg
        if name == "out" and not deprecated:
            type_str = f"{type_str} | None".replace(" | None | None", " | None")

        # pyi deprecated signatures don't get defaults for their out arg
        treat_as_no_default = (
            deprecated
            and isinstance(self, PythonOutArgument)
            and self.default == "None"
        )

        # add default
        if self.default is not None and not treat_as_no_default:
            if (
                isinstance(self.type, ListType)
                and self.type.elem == BaseType(BaseTy.int)
                and self.default.startswith("{")
                and self.default.endswith("}")
            ):
                default = (
                    "(" + ", ".join(map(str.strip, self.default[1:-1].split(","))) + ")"
                )
            else:
                default = {
                    "nullptr": "None",
                    "::std::nullopt": "None",
                    "std::nullopt": "None",
                    "{}": "None",
                    "c10::MemoryFormat::Contiguous": "contiguous_format",
                    "QScheme::PER_TENSOR_AFFINE": "per_tensor_affine",
                }.get(self.default, self.default)
            return f"{name}: {type_str} = {default}"
        else:
            return f"{name}: {type_str}"