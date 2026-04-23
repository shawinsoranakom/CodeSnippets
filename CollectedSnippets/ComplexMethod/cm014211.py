def call_function(
        self,
        tx: "InstructionTranslator",
        args: Sequence["VariableTracker"],
        kwargs: "dict[str, VariableTracker]",
    ) -> "VariableTracker":
        # See also: module `torch._dynamo.polyfills.itertools`

        if self.value is itertools.product:
            if any(kw != "repeat" for kw in kwargs):
                unimplemented(
                    gb_type="Unsupported kwargs for itertools.product",
                    context=f"call_function {self} {args} {kwargs}",
                    explanation=f"Expected kwargs: 'repeat', but got "
                    f"{','.join(set(kwargs.keys()) - {'repeat'})}",
                    hints=[*graph_break_hints.USER_ERROR],
                )

            if "repeat" in kwargs:
                r = kwargs["repeat"].as_python_constant()
            else:
                r = 1
            seqs = [arg.force_unpack_var_sequence(tx) for arg in args]
            items = [
                variables.TupleVariable(list(item))
                for item in itertools.product(*seqs, repeat=r)
            ]
            return variables.ListIteratorVariable(
                items,  # type: ignore[arg-type]
                mutation_type=ValueMutationNew(),
            )
        elif (
            self.value is itertools.combinations
            and not kwargs
            and len(args) == 2
            and args[0].has_unpack_var_sequence(tx)
            and args[1].is_python_constant()
        ):
            iterable = args[0].unpack_var_sequence(tx)
            r = args[1].as_python_constant()

            items = []
            for item in itertools.combinations(iterable, r):
                items.append(variables.TupleVariable(list(item)))
            return variables.ListIteratorVariable(
                items,  # type: ignore[arg-type]
                mutation_type=ValueMutationNew(),
            )
        elif self.value is itertools.groupby:
            if any(kw != "key" for kw in kwargs):
                unimplemented(
                    gb_type="Unsupported kwargs for itertools.groupby",
                    context=f"call_function {self} {args} {kwargs}",
                    explanation=f"Expected kwargs: 'key', but got "
                    f"{','.join(set(kwargs.keys()) - {'key'})}",
                    hints=[*graph_break_hints.USER_ERROR],
                )

            def retrieve_const_key(key: VariableTracker) -> Any:
                if isinstance(key, variables.SymNodeVariable):
                    return key.evaluate_expr()
                elif key.is_python_constant():
                    return key.as_python_constant()
                else:
                    unimplemented(
                        gb_type="Unsupported key type for itertools.groupby",
                        context=f"call_function {self} {args} {kwargs}",
                        explanation="Dynamo does not know how to trace "
                        f"itertools.groupby with key type: {str(type(key))}. "
                        "We only support grouping keys that are constants (int, float, str, etc.)",
                        hints=[*graph_break_hints.SUPPORTABLE],
                    )

            if len(args) == 1 and args[0].has_unpack_var_sequence(tx):
                seq = args[0].unpack_var_sequence(tx)
            else:
                unimplemented(
                    gb_type="Unsupported arguments for itertools.groupby",
                    context=f"call_function {self} {args} {kwargs}",
                    explanation="Dynamo does not know how to trace "
                    f"itertools.groupby with args: {args} and kwargs: {kwargs}. "
                    "itertools.groupby expects an iterable to group and an "
                    "optional key function to determine groupings.",
                    hints=[
                        "Make sure the arguments to itertools.groupby are correct.",
                        *graph_break_hints.SUPPORTABLE,
                    ],
                )

            if "key" in kwargs:

                def keyfunc(x: VariableTracker) -> Any:
                    return retrieve_const_key(
                        kwargs.get("key").call_function(tx, [x], {})  # type: ignore[union-attr]
                    )

            else:

                def keyfunc(x: VariableTracker) -> Any:
                    return retrieve_const_key(x)

            result = []
            try:
                for k, v in itertools.groupby(seq, key=keyfunc):
                    result.append(
                        variables.TupleVariable(
                            [
                                (
                                    variables.ConstantVariable.create(k)
                                    if variables.ConstantVariable.is_literal(k)
                                    else k
                                ),
                                variables.ListIteratorVariable(
                                    list(v), mutation_type=ValueMutationNew()
                                ),
                            ],
                            mutation_type=ValueMutationNew(),
                        )
                    )
            except Exception as e:
                unimplemented(
                    gb_type="Unexpected failure during itertools.groupby() iteration",
                    context=f"call_function {self} {args} {kwargs}",
                    explanation="Unexpected failure in invoking function during groupby",
                    hints=[*graph_break_hints.SUPPORTABLE],
                    from_exc=e,
                )
            return variables.ListIteratorVariable(
                result,  # type: ignore[arg-type]
                mutation_type=ValueMutationNew(),
            )
        elif self.value is itertools.repeat:
            if len(args) < 2:
                return variables.RepeatIteratorVariable(
                    *args, mutation_type=ValueMutationNew()
                )

            return tx.inline_user_function_return(
                VariableTracker.build(tx, polyfills.repeat), args, kwargs
            )
        elif self.value is itertools.count and not kwargs:
            if len(args) == 0:
                return variables.CountIteratorVariable(mutation_type=ValueMutationNew())
            if len(args) == 1:
                return variables.CountIteratorVariable(
                    item=args[0], mutation_type=ValueMutationNew()
                )
            if len(args) == 2:
                return variables.CountIteratorVariable(
                    item=args[0],
                    step=args[1],
                    mutation_type=ValueMutationNew(),
                )
            return super().call_function(tx, args, kwargs)
        elif (
            self.value is itertools.permutations
            and (len(args) == 1 or (len(args) == 2 and args[1].is_python_constant()))
            and not kwargs
        ):
            if len(args) == 2:
                r = args[1].as_python_constant()
            else:
                r = None
            items = [
                variables.TupleVariable(list(item))
                for item in itertools.permutations(
                    args[0].force_unpack_var_sequence(tx), r
                )
            ]
            return variables.ListIteratorVariable(
                items,  # type: ignore[arg-type]
                mutation_type=ValueMutationNew(),
            )
        else:
            return super().call_function(tx, args, kwargs)