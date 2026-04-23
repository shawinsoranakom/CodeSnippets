def bind_args(
        self,
        parent: "InstructionTranslator",
        args: Sequence[VariableTracker],
        kwargs: dict[str, VariableTracker],
    ) -> dict[str, VariableTracker]:
        """
        Assume `args` and `kwargs` are VariableTracker arguments for a call to
        this function, create new bindings for initial locals.
        """
        assert not self.is_constant

        fn: types.FunctionType = self.fn

        if not isinstance(fn, FunctionType):
            raise TypeError("Only supports regular Python functions.")
        root_tx = parent.output.root_tx

        source = self.get_source()
        result = bind_args_cached(fn, root_tx, source, args, kwargs)  # type: ignore[arg-type]

        init_cellvars(parent, result, fn.__code__)
        closure = self.fn.__closure__ or ()
        assert len(closure) == len(self.fn.__code__.co_freevars)
        for idx, name, cell in zip(
            itertools.count(), self.fn.__code__.co_freevars, closure
        ):
            # TODO refactor these 3 branches.
            side_effects = parent.output.side_effects
            if cell in side_effects:
                cell_var = side_effects[cell]

            elif source:
                closure_cell = GetItemSource(ClosureSource(source), idx)
                closure_cell_contents = CellContentsSource(
                    closure_cell, "cell_contents", freevar_name=name
                )
                try:
                    contents_var = VariableTracker.build(
                        parent, cell.cell_contents, closure_cell_contents
                    )
                except ValueError:
                    # Cell has not yet been assigned
                    contents_var = variables.DeletedVariable()
                cell_var = side_effects.track_cell_existing(
                    closure_cell, cell, contents_var
                )

            else:
                # TODO figure out why source isn't available here, and whether
                # we can fix that and remove this branch.
                try:
                    contents_var = VariableTracker.build(parent, cell.cell_contents)
                except ValueError:
                    # Cell has not yet been assigned
                    contents_var = variables.DeletedVariable()
                cell_var = side_effects.track_cell_existing(None, cell, contents_var)

            result[name] = cell_var

        return result