def call_function(
        self,
        tx: "InstructionTranslator",
        args: Sequence[VariableTracker],
        kwargs: dict[str, VariableTracker],
    ) -> VariableTracker:
        if self.can_constant_fold_through() and check_unspec_or_constant_args(
            args, kwargs
        ):
            result = (
                self.fn(  # use the original function which is faster than the polyfill
                    *[x.as_python_constant() for x in args],
                    **{k: v.as_python_constant() for k, v in kwargs.items()},
                )
            )
            return VariableTracker.build(tx, result)

        # Special case for sum on tuple/list of ints
        if (
            self.fn is builtins.sum
            and len(args) == 1
            and not kwargs
            and isinstance(args[0], (variables.ListVariable, variables.TupleVariable))
            and all(
                (x.is_python_constant() and isinstance(x.as_python_constant(), int))
                or (isinstance(x, variables.SymNodeVariable) and x.python_type() is int)
                for x in args[0].items
            )
        ):
            return variables.SymNodeVariable.create(
                tx,
                tx.output.create_proxy(
                    "call_function",
                    torch.sym_sum,
                    (tuple(a.as_proxy() for a in args[0].items),),
                    {},
                ),
                sym_num=torch.sym_sum(
                    [
                        (
                            x.as_python_constant()
                            if x.is_python_constant()
                            else x.sym_num  # type: ignore[attr-defined]
                        )
                        for x in args[0].items
                    ]
                ),
            )

        traceable_function_variable = VariableTracker.build(tx, self.traceable_fn)
        return traceable_function_variable.call_function(tx, args, kwargs)