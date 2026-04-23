def build_template_from_method(
    class_name: str,
    method_name: str,
    type_to_cls_dict: dict,
    *,
    add_function: bool = False,
):
    classes = [item.__name__ for item in type_to_cls_dict.values()]

    # Raise error if class_name is not in classes
    if class_name not in classes:
        msg = f"{class_name} not found."
        raise ValueError(msg)

    for _type, v in type_to_cls_dict.items():
        if v.__name__ == class_name:
            class_ = v

            # Check if the method exists in this class
            if not hasattr(class_, method_name):
                msg = f"Method {method_name} not found in class {class_name}"
                raise ValueError(msg)

            # Get the method
            method = getattr(class_, method_name)

            # Get the docstring
            docs = parse(method.__doc__)

            # Get the signature of the method
            sig = inspect.signature(method)

            # Get the parameters of the method
            params = sig.parameters

            # Initialize the variables dictionary with method parameters
            variables = {
                "_type": _type,
                **{
                    name: {
                        "default": (param.default if param.default != param.empty else None),
                        "type": (param.annotation if param.annotation != param.empty else None),
                        "required": param.default == param.empty,
                    }
                    for name, param in params.items()
                    if name not in {"self", "kwargs", "args"}
                },
            }

            base_classes = get_base_classes(class_)

            # Adding function to base classes to allow the output to be a function
            if add_function:
                base_classes.append("Callable")

            return {
                "template": format_dict(variables, class_name),
                "description": docs.short_description or "",
                "base_classes": base_classes,
            }
    return None