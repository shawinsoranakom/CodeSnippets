def decorator(func):
        if iscoroutinefunction(func):
            sensitive_variables_wrapper = func

            wrapped_func = func
            while getattr(wrapped_func, "__wrapped__", None) is not None:
                wrapped_func = wrapped_func.__wrapped__

            try:
                file_path = inspect.getfile(wrapped_func)
            except TypeError:  # Raises for builtins or native functions.
                raise ValueError(
                    f"{func.__name__} cannot safely be wrapped by "
                    "@sensitive_variables, make it either non-async or defined in a "
                    "Python file (not a builtin or from a native extension)."
                )
            else:
                # A source file may not be available (e.g. in .pyc-only
                # builds), use the first line number instead.
                first_line_number = wrapped_func.__code__.co_firstlineno
                key = hash(f"{file_path}:{first_line_number}")

            if variables:
                coroutine_functions_to_sensitive_variables[key] = variables
            else:
                coroutine_functions_to_sensitive_variables[key] = "__ALL__"

        else:

            @wraps(func)
            def sensitive_variables_wrapper(*func_args, **func_kwargs):
                if variables:
                    sensitive_variables_wrapper.sensitive_variables = variables
                else:
                    sensitive_variables_wrapper.sensitive_variables = "__ALL__"
                return func(*func_args, **func_kwargs)

        return sensitive_variables_wrapper