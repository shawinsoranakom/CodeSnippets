def visit(
        cls,
        fn: Callable[[VariableTracker], None],
        value: Any,
        cache: dict[int, Any] | None = None,
        side_effects: SideEffects | None = None,
    ) -> None:
        """
        Walk value and call fn on all the VariableTracker instances.

        When side_effects is provided, also walks attributes stored in
        store_attr_mutations (e.g. dataclass fields set during tracing
        that aren't in the VT's __dict__).
        """
        if cache is None:
            cache = {}

        idx = id(value)
        if idx in cache:
            return
        # save `value` to keep it alive and ensure id() isn't reused
        cache[idx] = value

        if isinstance(value, VariableTracker):
            value = value.unwrap()
            fn(value)
            value = value.unwrap()  # calling fn() might have realized it
            nonvars = value._nonvar_fields
            for key, subvalue in value.__dict__.items():
                if key not in nonvars:
                    cls.visit(fn, subvalue, cache, side_effects)
            if side_effects is not None and value in side_effects.store_attr_mutations:
                for attr_vt in side_effects.store_attr_mutations[value].values():
                    cls.visit(fn, attr_vt, cache, side_effects)
        elif istype(value, (list, tuple)):
            for subvalue in value:
                cls.visit(fn, subvalue, cache, side_effects)
        elif istype(value, (dict, collections.OrderedDict)):
            for subvalue in value.values():
                cls.visit(fn, subvalue, cache, side_effects)