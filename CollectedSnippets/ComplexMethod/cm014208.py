def var_getattr(self, tx: "InstructionTranslator", name: str) -> VariableTracker:
        # NB: This INTENTIONALLY does not call super(), because there is
        # no intrinsic reason ndarray properties are related to Tensor
        # properties.  The inheritance here is for implementation sharing.

        from ..utils import numpy_attr_wrapper
        from .builder import wrap_fx_proxy

        result = None

        example_value = self.as_proxy().node.meta["example_value"]
        example_ndarray = tnp.ndarray(example_value)

        def insert_into_graph() -> VariableTracker:
            return wrap_fx_proxy(
                tx,
                tx.output.create_proxy(
                    "call_function", numpy_attr_wrapper, (self.as_proxy(), name), {}
                ),
            )

        if name in ["T", "real", "imag", "flat"]:
            proxy = tx.output.create_proxy(
                "call_function",
                numpy_attr_wrapper,
                (self.as_proxy(), name),
                {},
            )
            result = NumpyNdarrayVariable.create(tx, proxy)

        # These are awkward to implement.  The standard playbook for torch._numpy
        # interop is to trace a call into the torch._numpy wrapper which works for
        # Tensor operations.  However, we don't want to do this for calls
        # that don't return Tensors, because in those cases we may not want
        # to trace the attribute access into the graph at all (it is sort
        # of harmless to do so, because AOTAutograd will eliminate them,
        # but it's best not to trace them in to begin with.)  But in any
        # case, tracing these into the graph is like trying to fit a square
        # peg into a round hole; best not to do it.  So instead we
        # painstakingly implement these by hand
        #
        # NB: only ALWAYS specialized attributes can go here; notably,
        # size/shape not allowed!
        elif name in ("ndim", "itemsize"):
            return VariableTracker.build(tx, getattr(example_ndarray, name))
        elif name in ("shape", "stride"):
            if not has_free_symbols(r := getattr(example_ndarray, name)):
                return VariableTracker.build(tx, tuple(int(r) for r in r))
            return insert_into_graph()
        elif name == "size":
            if not has_free_symbols(r := example_ndarray.size):
                return VariableTracker.build(tx, int(r))
            return insert_into_graph()
        elif name in ["base", "flags", "dtype"]:
            unimplemented(
                gb_type="Unsupported ndarray attribute access",
                context=f"var_getattr {self} {name}",
                explanation=f"Dynamo currently does not support tracing `ndarray.{name}`.",
                hints=[],
            )
        elif name == "__version__":
            unimplemented(
                gb_type="Unsupported ndarray.__version__ access",
                context=f"var_getattr {self} {name}",
                explanation=f"Dynamo currently does not support tracing `ndarray.{name}`.",
                hints=[],
            )
        if result is None:
            raise NotImplementedError
        return result