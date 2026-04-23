def wrapper(*args: Any, **kwargs: Any) -> Any:
            """Validate exactly one arg in each group is not None."""
            counts = [
                sum(1 for arg in arg_group if kwargs.get(arg) is not None)
                for arg_group in arg_groups
            ]
            invalid_groups = [i for i, count in enumerate(counts) if count != 1]
            if invalid_groups:
                invalid_group_names = [", ".join(arg_groups[i]) for i in invalid_groups]
                msg = (
                    "Exactly one argument in each of the following"
                    " groups must be defined:"
                    f" {', '.join(invalid_group_names)}"
                )
                raise ValueError(msg)
            return func(*args, **kwargs)