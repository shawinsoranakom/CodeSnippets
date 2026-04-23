def __init__(self, signature, call_context_args, args, kwargs):
        # Strip out user-supplied call-context args that this layer’s `call()`
        # does not accept (otherwise `signature.bind` would raise).
        # This includes built-in args like `training`, and user-defined args.
        call_args = {
            context_arg: kwargs.pop(context_arg)
            for context_arg in call_context_args
            if context_arg in kwargs and context_arg not in signature.parameters
        }

        bound_args = signature.bind(*args, **kwargs)

        # Combine the two dicts.
        self.user_arguments_dict = {**call_args, **bound_args.arguments}

        bound_args.apply_defaults()
        arg_dict = {}
        arg_names = []
        tensor_arg_dict = {}
        tensor_args = []
        tensor_arg_names = []
        nested_tensor_arg_names = []
        for name, value in bound_args.arguments.items():
            arg_dict[name] = value
            arg_names.append(name)
            if is_backend_tensor_or_symbolic(value):
                tensor_args.append(value)
                tensor_arg_names.append(name)
                tensor_arg_dict[name] = value
            elif tree.is_nested(value) and len(value) > 0:
                flat_values = tree.flatten(value)
                if all(
                    is_backend_tensor_or_symbolic(x, allow_none=True)
                    for x in flat_values
                ):
                    tensor_args.append(value)
                    tensor_arg_names.append(name)
                    tensor_arg_dict[name] = value
                    nested_tensor_arg_names.append(name)
                elif any(is_backend_tensor_or_symbolic(x) for x in flat_values):
                    raise ValueError(
                        "In a nested call() argument, "
                        "you cannot mix tensors and non-tensors. "
                        "Received invalid mixed argument: "
                        f"{name}={value}"
                    )
        self.arguments_dict = arg_dict
        self.argument_names = arg_names
        self.tensor_arguments_dict = tensor_arg_dict
        self.tensor_arguments_names = tensor_arg_names
        self.nested_tensor_argument_names = nested_tensor_arg_names
        self.first_arg = arg_dict[arg_names[0]]
        if all(
            backend.is_tensor(x) for x in self.tensor_arguments_dict.values()
        ):
            self.eager = True
        else:
            self.eager = False