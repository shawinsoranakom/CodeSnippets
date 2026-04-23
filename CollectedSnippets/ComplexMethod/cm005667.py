def wrapped_func(*args, **kwargs):
            # Get class + function name (just for better warning message)
            func_name = func.__name__
            if is_instance_method:
                func_name = f"{args[0].__class__.__name__}.{func_name}"
            elif is_class_method:
                func_name = f"{args[0].__name__}.{func_name}"

            minimum_action = Action.NONE
            message = None

            # deprecated kwarg and its new version are set for function call -> replace it with new name
            if old_name in kwargs and new_name in kwargs:
                minimum_action = Action.RAISE if raise_if_both_names else Action.NOTIFY_ALWAYS
                message = f"Both `{old_name}` and `{new_name}` are set for `{func_name}`. Using `{new_name}={kwargs[new_name]}` and ignoring deprecated `{old_name}={kwargs[old_name]}`."
                kwargs.pop(old_name)

            # only deprecated kwarg is set for function call -> replace it with new name
            elif old_name in kwargs and new_name is not None and new_name not in kwargs:
                minimum_action = Action.NOTIFY
                message = f"`{old_name}` is deprecated {version_message} for `{func_name}`. Use `{new_name}` instead."
                kwargs[new_name] = kwargs.pop(old_name)

            # deprecated kwarg is not set for function call and new name is not specified -> just notify
            elif old_name in kwargs:
                minimum_action = Action.NOTIFY
                message = f"`{old_name}` is deprecated {version_message} for `{func_name}`."

            if message is not None and additional_message is not None:
                message = f"{message} {additional_message}"

            # update minimum_action if argument is ALREADY deprecated (current version >= deprecated version)
            if is_greater_or_equal_version:
                # change to (NOTIFY, NOTIFY_ALWAYS) -> RAISE if specified
                # in case we want to raise error for already deprecated arguments
                if raise_if_greater_or_equal_version and minimum_action != Action.NONE:
                    minimum_action = Action.RAISE

                # change to NOTIFY -> NONE if specified (NOTIFY_ALWAYS can't be changed to NONE)
                # in case we want to ignore notifications for already deprecated arguments
                elif not warn_if_greater_or_equal_version and minimum_action == Action.NOTIFY:
                    minimum_action = Action.NONE

            # raise error or notify user
            if minimum_action == Action.RAISE:
                raise ValueError(message)
            # If we are compiling, we do not raise the warning as it would break compilation
            elif minimum_action in (Action.NOTIFY, Action.NOTIFY_ALWAYS) and not is_torchdynamo_compiling():
                # DeprecationWarning is ignored by default, so we use FutureWarning instead
                warnings.warn(message, FutureWarning, stacklevel=2)

            return func(*args, **kwargs)