def _replace_args(
    old_args: tuple[Any, ...], new_args: tuple[Any, ...], argnums: argnums_t
) -> tuple[Any, ...]:
    if isinstance(argnums, int):
        if len(new_args) != 1:
            raise RuntimeError(
                f"new_args should be of size 1, was of size {len(new_args)}"
            )
        return tuple(
            new_args[0] if i == argnums else old_args[i] for i in range(len(old_args))
        )
    if isinstance(argnums, tuple):
        if len(new_args) != len(argnums):
            raise RuntimeError(
                "new_args should have the same size as argnums. "
                f"Argnums size {len(argnums)}, new_args size {len(new_args)}"
            )

        argnums_tuple = argnums

        def get_right_elem(i: int) -> Any:
            return (
                new_args[argnums_tuple.index(i)] if i in argnums_tuple else old_args[i]
            )

        return tuple(get_right_elem(i) for i in range(len(old_args)))
    raise RuntimeError(f"argnums must be int or Tuple[int, ...], got: {type(argnums)}")