def install_dict_contains_guard(
        self, tx: "InstructionTranslator", args: list[VariableTracker]
    ) -> None:
        # Key guarding - These are the cases to consider
        # 1) The dict has been mutated. In this case, we would have already
        # inserted a DICT_KEYS_MATCH guard, so we can skip.
        #
        # 2) args[0].source is None. This happens for const keys. Here, we
        # have to insert the DICT_CONTAINS guard.
        #
        # 3) args[0].source is not None. This can happen for non-const VTs.
        #   3a) contains=True. In this case, we can access the lazyVT from
        #   original_items and selectively realize it.
        #   3b) contains=False. There is no easy way to selectively apply this
        #   DICT_NOT_CONTAINS guard because our guard are represented via trees.
        #   Be conservative and add DICT_KEYS_MATCH guard.

        if not self.source:
            return

        if tx.output.side_effects.is_modified(self):
            return

        contains = args[0] in self
        if args[0].source is None and args[0].is_python_constant():
            guard_fn = (
                type(self).CONTAINS_GUARD if contains else type(self).NOT_CONTAINS_GUARD
            )
            install_guard(
                self.make_guard(
                    functools.partial(
                        guard_fn,
                        key=args[0].as_python_constant(),
                    )
                )
            )
        elif args[0].source:
            if contains:
                self.realize_key_vt(args[0])
            else:
                self.install_dict_keys_match_guard()