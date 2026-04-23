def var_getattr(self, tx: "InstructionTranslator", name: str):
        fn_dict = self.get_dict_vt(tx)

        # missing: __globals__, __closure__, __kwdefautls__, __defaults__
        if name in ("__name__", "__qualname__", "__doc__", "__module__", "__code__"):
            val = getattr(self, f"get_{name[2:-2]}")()
            if fn_dict.contains(name):
                return fn_dict.getitem(name)
            return ConstantVariable.create(
                val, source=self.source and AttrSource(self.source, name)
            )
        elif name == "__dict__":
            return fn_dict
        elif name == "__annotations__":
            return fn_dict.getitem_or_default(
                name,
                lambda: variables.ConstDictVariable(
                    {},
                    mutation_type=ValueMutationNew(),
                ),
            )
        elif name == "__type_params__":
            return fn_dict.getitem_or_default(
                name,
                lambda: variables.TupleVariable(
                    [],
                    mutation_type=ValueMutationNew(),
                ),
            )
        else:
            if fn_dict.contains(name):
                return fn_dict.getitem(name)
            else:
                raise_observed_exception(AttributeError, tx)