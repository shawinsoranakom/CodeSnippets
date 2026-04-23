def __new__(cls, *args, **kwargs):
        """We override __new__ to saving serializable constructor arguments.

        These arguments are used to auto-generate an object serialization
        config, which enables user-created subclasses to be serializable
        out of the box in most cases without forcing the user
        to manually implement `get_config()`.
        """
        instance = super(Operation, cls).__new__(cls)
        if backend.backend() == "jax" and is_nnx_enabled():
            from flax import nnx

            try:
                vars(instance)["_pytree__state"] = nnx.pytreelib.PytreeState()
            except AttributeError:
                vars(instance)["_object__state"] = nnx.object.ObjectState()

        # Generate a config to be returned by default by `get_config()`.
        auto_config = True

        signature = inspect.signature(cls.__init__)
        argspec = inspect.getfullargspec(cls.__init__)

        try:
            bound_parameters = signature.bind(None, *args, **kwargs)
        except TypeError:
            # Raised by signature.bind when the supplied args and kwargs
            # do not match the signature.
            auto_config = False

        if auto_config and any(
            [
                param.kind == inspect.Parameter.POSITIONAL_ONLY
                for name, param in signature.parameters.items()
                if name != argspec.args[0]
            ]
        ):
            # cls.__init__ takes positional only arguments, which
            # cannot be restored via cls(**config)
            auto_config = False
            # Create variable to show appropriate warning in get_config.
            instance._auto_config_error_args = True

        if auto_config:
            # Include default values in the config.
            bound_parameters.apply_defaults()
            # Extract all arguments as a dictionary.
            kwargs = bound_parameters.arguments
            # Expand variable kwargs argument.
            kwargs |= kwargs.pop(argspec.varkw, {})
            # Remove first positional argument, self.
            kwargs.pop(argspec.args[0])
            # Remove argument "name", as it is provided by get_config.
            kwargs.pop("name", None)
            if argspec.varargs is not None:
                # Varargs cannot be meaningfully converted to a dictionary.
                varargs = kwargs.pop(argspec.varargs)
                if len(varargs) > 0:
                    auto_config = False
                    # Store variable to show appropriate warning in get_config.
                    instance._auto_config_error_args = True

        # For safety, we only rely on auto-configs for a small set of
        # serializable types.
        supported_types = (str, int, float, bool, type(None))
        try:
            flat_arg_values = tree.flatten(kwargs)
            for value in flat_arg_values:
                if not isinstance(value, supported_types):
                    auto_config = False
                    break
        except TypeError:
            auto_config = False
        try:
            instance._lock = False
            if auto_config:
                from keras.src.saving import serialization_lib

                instance._auto_config = serialization_lib.SerializableDict(
                    **kwargs
                )
            else:
                instance._auto_config = None
            instance._lock = True
        except RecursionError:
            # Setting an instance attribute in __new__ has the potential
            # to trigger an infinite recursion if a subclass overrides
            # setattr in an unsafe way.
            pass
        return instance