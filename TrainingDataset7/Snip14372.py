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