def call_method(
        self,
        tx: "InstructionTranslator",
        name: str,
        args: list[VariableTracker],
        kwargs: dict[str, VariableTracker],
    ) -> VariableTracker:
        if name == "seed":
            tx.output.side_effects.mutation(self)
            self.random.seed(
                *[x.as_python_constant() for x in args],
                **{key: val.as_python_constant() for key, val in kwargs.items()},
            )
            return variables.ConstantVariable.create(None)
        elif name == "getstate":
            return self.wrap_state(self.random.getstate())
        elif name == "setstate":
            tx.output.side_effects.mutation(self)
            self.random.setstate(self.unwrap_state(args[0]))
            return variables.ConstantVariable.create(None)
        elif name in self._supported_fn_names:
            tx.output.side_effects.mutation(self)
            state = self.random.getstate()

            def call_random_meth(*args: Any, **kwargs: Any) -> Any:
                r = random.Random()
                r.setstate(state)
                return getattr(r, name)(*args, **kwargs)

            # self.random state not actually updated by call_random_meth, so update here
            # by calling the method
            getattr(self.random, name)(
                *[x.as_python_constant() for x in args],
                **{k: v.as_python_constant() for k, v in kwargs.items()},
            )

            return call_random_fn(tx, call_random_meth, args, kwargs)
        return super().call_method(tx, name, args, kwargs)