def get_field_type(
        field_type: Any,
        is_required: bool,
        target: Literal["docstring", "website"] = "docstring",
    ) -> str:
        """Get the implicit data type of a defined Pydantic field.
        Parameters
        ----------
        field_type : Any
            Typing object containing the field type.
        is_required : bool
            Flag to indicate if the field is required.
        target : Literal["docstring", "website"]
            Target to return type for. Defaults to "docstring".
        Returns
        -------
        str
            String representation of the field type.
        """
        is_optional = not is_required

        try:
            _type = field_type

            # Unwrap ForwardRef to its inner string
            if hasattr(_type, "__forward_arg__"):
                _type = _type.__forward_arg__

            if "BeforeValidator" in str(_type):
                _type = "Optional[int]" if is_optional else "int"  # type: ignore

            origin = get_origin(_type)
            if origin is Union:
                args = get_args(_type)
                type_names = []
                has_none = False
                for arg in args:
                    if arg is type(None):
                        has_none = True
                        continue
                    if get_origin(arg) is Literal:
                        continue
                    type_name = str(arg)
                    if hasattr(arg, "__name__"):
                        type_name = arg.__name__
                    type_name = (
                        type_name.replace("typing.", "")
                        .replace("pydantic.types.", "")
                        .replace("datetime.datetime", "datetime")
                        .replace("datetime.date", "date")
                    )
                    if "openbb_" in type_name:
                        type_name = type_name.rsplit(".", 1)[-1]
                    if type_name != "NoneType":
                        type_names.append(type_name)

                unique_types = sorted(list(set(type_names)))
                if has_none:
                    unique_types.append("None")
                _type = " | ".join(unique_types)
            else:
                _type = (
                    str(_type)
                    .replace("<class '", "")
                    .replace("'>", "")
                    .replace("typing.", "")
                    .replace("pydantic.types.", "")
                    .replace("datetime.datetime", "datetime")
                    .replace("datetime.date", "date")
                    .replace("NoneType", "None")
                    .replace(", None", "")
                )

            if "openbb_" in str(_type):
                _type = (
                    str(_type).split(".", maxsplit=1)[0].split("openbb_")[0]
                    + str(_type).rsplit(".", maxsplit=1)[-1]
                )

            _type = (
                f"Optional[{_type}]"
                if is_optional
                and "Optional" not in str(_type)
                and " | " not in str(_type)
                else _type
            )

            if target == "website":
                _type = re.sub(r"Optional\[(.*)\]", r"\1", _type)

            return _type

        except TypeError:
            return str(field_type)