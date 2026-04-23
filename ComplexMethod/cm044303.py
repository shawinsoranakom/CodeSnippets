def stringify_param(param: Parameter) -> str:
            """Format a parameter as a string."""
            if not (
                isinstance(param.annotation, _AnnotatedAlias)
                and any(
                    isinstance(m, OpenBBField) for m in param.annotation.__metadata__
                )
            ):
                return str(param)

            type_hint = param.annotation.__args__[0]
            type_repr = get_type_repr(type_hint)
            meta = next(
                m for m in param.annotation.__metadata__ if isinstance(m, OpenBBField)
            )
            desc = meta.description
            desc_repr = repr(desc)

            if desc is None:
                desc = ""
            # For function signatures, use shorter max width to prevent line overflow
            max_width = 50

            if len(desc) <= max_width:
                desc_repr = repr(desc)
            else:
                parts = textwrap.wrap(desc, width=max_width)
                # For function signature context, don't add extra indentation
                # The parameter will be properly indented by the calling context
                joined = "\n                    ".join(f"{repr(p)}" for p in parts)
                desc_repr = f"(\n                    {joined}" + "\n                )"

            default_part = ""

            if param.default is not Parameter.empty:
                default_repr = repr(param.default)
                if default_repr == "Ellipsis":
                    default_repr = "None"
                default_part = f" = {default_repr}"
            if (
                "None" in default_part
                and "| None" not in type_repr
                and "Optional" not in type_repr
            ):
                type_repr += " | None"
            final_param = f"""{param.name.strip()}: Annotated[
            {type_repr},
            OpenBBField(
                description={desc_repr}
            )
        ]{default_part}"""

            return final_param