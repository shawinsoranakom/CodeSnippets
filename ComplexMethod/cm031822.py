def validate_uop(override: Uop, uop: Uop) -> None:
    """
    Check that the overridden uop (defined in 'optimizer_bytecodes.c')
    has the same stack effects as the original uop (defined in 'bytecodes.c').

    Ensure that:
        - The number of inputs and outputs is the same.
        - The names of the inputs and outputs are the same
          (except for 'unused' which is ignored).
        - The sizes of the inputs and outputs are the same.
    """
    for stack_effect in ('inputs', 'outputs'):
        orig_effects = getattr(uop.stack, stack_effect)
        new_effects = getattr(override.stack, stack_effect)

        if len(orig_effects) != len(new_effects):
            msg = (
                f"{uop.name}: Must have the same number of {stack_effect} "
                "in bytecodes.c and optimizer_bytecodes.c "
                f"({len(orig_effects)} != {len(new_effects)})"
            )
            raise analysis_error(msg, override.body.open)

        for orig, new in zip(orig_effects, new_effects, strict=True):
            if orig.name != new.name and orig.name != "unused" and new.name != "unused":
                msg = (
                    f"{uop.name}: {stack_effect.capitalize()} must have "
                    "equal names in bytecodes.c and optimizer_bytecodes.c "
                    f"({orig.name} != {new.name})"
                )
                raise analysis_error(msg, override.body.open)

            if orig.size != new.size:
                msg = (
                    f"{uop.name}: {stack_effect.capitalize()} must have "
                    "equal sizes in bytecodes.c and optimizer_bytecodes.c "
                    f"({orig.size!r} != {new.size!r})"
                )
                raise analysis_error(msg, override.body.open)