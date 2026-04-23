def call_method(
        self,
        tx: "InstructionTranslator",
        name: str,
        args: list[VariableTracker],
        kwargs: dict[str, VariableTracker],
    ) -> VariableTracker:
        if name == "size":
            if args or kwargs:
                raise_args_mismatch(
                    tx,
                    name,
                    "0 args and 0 kwargs",
                    f"{len(args)} args and {len(kwargs)} kwargs",
                )
            result = self.example_value.size()
            if not has_free_symbols(result):
                # avoid creating a node in the graph
                return VariableTracker.build(tx, int(result))
            else:
                from ..external_utils import untyped_storage_size
                from .builder import wrap_fx_proxy

                return wrap_fx_proxy(
                    tx,
                    tx.output.create_proxy(
                        "call_function",
                        untyped_storage_size,
                        (self.from_tensor.as_proxy(),),
                        {},
                    ),
                )
        if name == "resize_" and len(args) == 1:
            if kwargs:
                raise_args_mismatch(tx, name, "0 kwargs", f"{len(kwargs)} kwargs")
            tx.output.create_proxy(
                "call_function",
                torch.ops.inductor.resize_storage_bytes_,
                (self.from_tensor.as_proxy(), args[0].as_proxy()),
                {},
            )
            return self

        return super().call_method(tx, name, args, kwargs)