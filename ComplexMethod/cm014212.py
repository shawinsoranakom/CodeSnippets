def next_variable(self, tx: "InstructionTranslator") -> VariableTracker:
        assert self.is_mutable()

        if len(self.iterables) == 0:
            raise_observed_exception(StopIteration, tx)

        old_index = self.index
        args = []

        def get_item(
            it: list[VariableTracker] | VariableTracker,
        ) -> VariableTracker:
            if isinstance(it, list):
                if old_index >= len(it):
                    raise_observed_exception(StopIteration, tx)
                return it[old_index]
            else:
                return it.next_variable(tx)

        idx: int | None = None
        try:
            for idx, it in enumerate(self.iterables):
                args.append(get_item(it))
        except ObservedUserStopIteration:
            if self.strict:
                if idx == 0:
                    # all other iterables should be exhausted
                    for it in self.iterables:
                        try:
                            get_item(it)
                        except ObservedUserStopIteration:
                            handle_observed_exception(tx)
                            continue
                        # no ObservedUserStopIteration - fall through to UserError
                        break
                    else:
                        # all iterables exhausted, raise original error
                        raise
                handle_observed_exception(tx)
                raise UserError(
                    ValueError,  # type: ignore[arg-type]
                    "zip() has one argument of len differing from others",
                ) from None
            raise

        tx.output.side_effects.mutation(self)
        self.index += 1
        return variables.TupleVariable(args)