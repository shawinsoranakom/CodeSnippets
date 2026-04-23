def decorator(func):
        if isinstance(func, type):
            raise TypeError(
                "@deprecate_posargs cannot be applied to a class. (Apply it "
                "to the __init__ method.)"
            )
        if isinstance(func, classmethod):
            raise TypeError("Apply @classmethod before @deprecate_posargs.")
        if isinstance(func, staticmethod):
            raise TypeError("Apply @staticmethod before @deprecate_posargs.")

        params = signature(func).parameters
        num_by_kind = Counter(param.kind for param in params.values())

        if num_by_kind[inspect.Parameter.VAR_POSITIONAL] > 0:
            raise TypeError(
                "@deprecate_posargs() cannot be used with variable positional `*args`."
            )

        num_positional_params = (
            num_by_kind[inspect.Parameter.POSITIONAL_ONLY]
            + num_by_kind[inspect.Parameter.POSITIONAL_OR_KEYWORD]
        )
        num_keyword_only_params = num_by_kind[inspect.Parameter.KEYWORD_ONLY]
        if num_keyword_only_params < 1:
            raise TypeError(
                "@deprecate_posargs() requires at least one keyword-only parameter "
                "(after a `*` entry in the parameters list)."
            )
        if any(
            name not in params or params[name].kind != inspect.Parameter.KEYWORD_ONLY
            for name in remappable_names
        ):
            raise TypeError(
                "@deprecate_posargs() requires all remappable_names to be "
                "keyword-only parameters."
            )

        num_remappable_args = len(remappable_names)
        max_positional_args = num_positional_params + num_remappable_args

        func_name = func.__name__
        if func_name == "__init__":
            # In the warning, show "ClassName()" instead of "__init__()".
            # The class isn't defined yet, but its name is in __qualname__.
            # Some examples of __qualname__:
            # - ClassName.__init__
            # - Nested.ClassName.__init__
            # - MyTests.test_case.<locals>.ClassName.__init__
            local_name = func.__qualname__.rsplit("<locals>.", 1)[-1]
            class_name = local_name.replace(".__init__", "")
            func_name = class_name

        def remap_deprecated_args(args, kwargs):
            """
            Move deprecated positional args to kwargs and issue a warning.
            Return updated (args, kwargs).
            """
            if (num_positional_args := len(args)) > max_positional_args:
                raise TypeError(
                    f"{func_name}() takes at most {max_positional_args} positional "
                    f"argument(s) (including {num_remappable_args} deprecated) but "
                    f"{num_positional_args} were given."
                )

            # Identify which of the _potentially remappable_ params are
            # actually _being remapped_ in this particular call.
            remapped_names = remappable_names[
                : num_positional_args - num_positional_params
            ]
            conflicts = set(remapped_names) & set(kwargs)
            if conflicts:
                # Report duplicate names in the original parameter order.
                conflicts_str = ", ".join(
                    f"'{name}'" for name in remapped_names if name in conflicts
                )
                raise TypeError(
                    f"{func_name}() got both deprecated positional and keyword "
                    f"argument values for {conflicts_str}."
                )

            # Do the remapping.
            remapped_kwargs = dict(
                zip(remapped_names, args[num_positional_params:], strict=True)
            )
            remaining_args = args[:num_positional_params]
            updated_kwargs = kwargs | remapped_kwargs

            # Issue the deprecation warning.
            remapped_names_str = ", ".join(f"'{name}'" for name in remapped_names)
            warnings.warn(
                f"Passing positional argument(s) {remapped_names_str} to {func_name}() "
                "is deprecated. Use keyword arguments instead.",
                deprecation_warning,
                skip_file_prefixes=django_file_prefixes(),
            )

            return remaining_args, updated_kwargs

        if iscoroutinefunction(func):

            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                if len(args) > num_positional_params:
                    args, kwargs = remap_deprecated_args(args, kwargs)
                return await func(*args, **kwargs)

        else:

            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                if len(args) > num_positional_params:
                    args, kwargs = remap_deprecated_args(args, kwargs)
                return func(*args, **kwargs)

        return wrapper