def create(value: Any, **kwargs: Any) -> VariableTracker:
        """
        Create a `ConstantVariable` based on the given value, and supports
        automatic routing for collection types like `tuple` (in which case we'd
        create `ConstantVariable` for the leaf items).

        NOTE: the caller must install the proper guards if needed; most often
        the guard will be `CONSTANT_MATCH`.
        """
        # Return pre-allocated sentinels for None/True/False when there are
        # no extra kwargs (source, etc.) that would differentiate the instance.
        if not kwargs:
            match value:
                case None:
                    return CONSTANT_VARIABLE_NONE
                case True:
                    return CONSTANT_VARIABLE_TRUE
                case False:
                    return CONSTANT_VARIABLE_FALSE

        source = kwargs.get("source")

        # Routing for supported collection literals.
        if isinstance(value, set):
            items = [ConstantVariable.create(x) for x in value]
            return variables.SetVariable(items, **kwargs)  # type: ignore[arg-type]
        elif isinstance(value, frozenset):
            items = [ConstantVariable.create(x) for x in value]
            return variables.FrozensetVariable(items, **kwargs)  # type: ignore[arg-type]
        elif isinstance(value, slice):
            slice_args = (value.start, value.stop, value.step)
            slice_args_vars = tuple(ConstantVariable.create(arg) for arg in slice_args)
            return variables.SliceVariable(slice_args_vars, **kwargs)
        elif isinstance(value, (list, tuple)):
            items = []
            for i, x in enumerate(value):
                item_source = GetItemSource(source, i) if source else None
                items.append(
                    ConstantVariable.create(
                        x,
                        source=item_source,
                    )
                )
            return variables.BaseListVariable.cls_for(type(value))(items, **kwargs)

        return ConstantVariable(value, **kwargs)