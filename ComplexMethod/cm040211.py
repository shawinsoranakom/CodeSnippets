def _retrieve_class_or_fn(
    name, registered_name, module, obj_type, full_config, custom_objects=None
):
    # If there is a custom object registered via
    # `register_keras_serializable()`, that takes precedence.
    if obj_type == "function":
        custom_obj = object_registration.get_registered_object(
            name, custom_objects=custom_objects
        )
    else:
        custom_obj = object_registration.get_registered_object(
            registered_name, custom_objects=custom_objects
        )
    if custom_obj is not None:
        return custom_obj

    if module:
        # If it's a Keras built-in object,
        # we cannot always use direct import, because the exported
        # module name might not match the package structure
        # (e.g. experimental symbols).
        if module == "keras" or module.startswith("keras."):
            api_name = f"{module}.{name}"

            if api_name in LOADING_APIS:
                raise ValueError(
                    f"Cannot deserialize `{api_name}`, loading functions are "
                    "not allowed during deserialization"
                )

            obj = api_export.get_symbol_from_name(api_name)
            if obj is not None:
                return obj

        # Configs of Keras built-in functions do not contain identifying
        # information other than their name (e.g. 'acc' or 'tanh'). This special
        # case searches the Keras modules that contain built-ins to retrieve
        # the corresponding function from the identifying string.
        if obj_type == "function" and module == "builtins":
            for mod in BUILTIN_MODULES:
                obj = api_export.get_symbol_from_name(f"keras.{mod}.{name}")
                if obj is not None:
                    return obj

            # Workaround for serialization bug in Keras <= 3.6 whereby custom
            # functions would only be saved by name instead of registered name,
            # i.e. "name" instead of "package>name". This allows recent versions
            # of Keras to reload models saved with 3.6 and lower.
            if ">" not in name:
                separated_name = f">{name}"
                for custom_name, custom_object in custom_objects.items():
                    if custom_name.endswith(separated_name):
                        return custom_object

        # Otherwise, attempt to retrieve the class object given the `module`
        # and `class_name`. Import the module, find the class.
        package = module.split(".", maxsplit=1)[0]
        if package in {"keras", "keras_hub", "keras_cv", "keras_nlp"}:
            try:
                mod = importlib.import_module(module)
                obj = vars(mod).get(name, None)
                if isinstance(obj, type) and issubclass(obj, KerasSaveable):
                    return obj
                else:
                    raise ValueError(
                        f"Could not deserialize '{module}.{name}' because "
                        "it is not a KerasSaveable subclass"
                    )
            except ModuleNotFoundError:
                raise TypeError(
                    f"Could not deserialize {obj_type} '{name}' because "
                    f"its parent module {module} cannot be imported. "
                    f"Full object config: {full_config}"
                )

    raise TypeError(
        f"Could not locate {obj_type} '{name}'. Make sure custom classes and "
        "functions are decorated with "
        "`@keras.saving.register_keras_serializable()`. If they are already "
        "decorated, make sure they are all imported so that the decorator is "
        f"run before trying to load them. Full object config: {full_config}"
    )