def build_template_from_function(name: str, type_to_loader_dict: dict, *, add_function: bool = False):
    classes = [item.__annotations__["return"].__name__ for item in type_to_loader_dict.values()]

    # Raise error if name is not in chains
    if name not in classes:
        msg = f"{name} not found"
        raise ValueError(msg)

    for _type, v in type_to_loader_dict.items():
        if v.__annotations__["return"].__name__ == name:
            class_ = v.__annotations__["return"]

            # Get the docstring
            docs = parse(class_.__doc__)

            variables = {"_type": _type}
            for class_field_items, value in class_.model_fields.items():
                if class_field_items == "callback_manager":
                    continue
                variables[class_field_items] = {}
                for name_, value_ in value.__repr_args__():
                    if name_ == "default_factory":
                        try:
                            variables[class_field_items]["default"] = get_default_factory(
                                module=class_.__base__.__module__, function=value_
                            )
                        except Exception:  # noqa: BLE001
                            logger.debug(f"Error getting default factory for {value_}", exc_info=True)
                            variables[class_field_items]["default"] = None
                    elif name_ != "name":
                        variables[class_field_items][name_] = value_

                variables[class_field_items]["placeholder"] = docs.params.get(class_field_items, "")
            # Adding function to base classes to allow
            # the output to be a function
            base_classes = get_base_classes(class_)
            if add_function:
                base_classes.append("Callable")

            return {
                "template": format_dict(variables, name),
                "description": docs.short_description or "",
                "base_classes": base_classes,
            }
    return None