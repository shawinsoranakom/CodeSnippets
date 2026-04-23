def _call_min_max_binary(
        self,
        tx: "InstructionTranslator",
        a: VariableTracker | None,
        b: VariableTracker | None,
    ) -> VariableTracker | None:
        if a is None or b is None:
            # a or b could be none if we reduce and _call_min_max_binary failed
            # to return something
            return None
        if self.tensor_args(a, b):
            if not a.is_tensor():
                a, b = b, a
            assert a.is_tensor()

            # result of an item call is a scalar convert to a tensor
            if isinstance(a, FakeItemVariable):
                a = variables.TorchInGraphFunctionVariable(torch.tensor).call_function(
                    tx, [a], {}
                )

            # Dynamic input does not get resolved, rather, gets stored as call_function
            if isinstance(a, SymNodeVariable) or isinstance(b, SymNodeVariable):
                from .builder import wrap_fx_proxy_cls

                return wrap_fx_proxy_cls(
                    type(a),
                    tx=tx,
                    proxy=tx.output.create_proxy(
                        "call_function",
                        self.fn,
                        *proxy_args_kwargs([a, b], {}),
                    ),
                )

            # convert min/max to torch ops
            if b.is_python_constant():
                fn: VariableTracker
                if isinstance(a, variables.NumpyNdarrayVariable):
                    import numpy as np

                    fn = variables.NumpyVariable(np.clip)
                else:
                    fn = variables.TorchInGraphFunctionVariable(torch.clamp)
                kwargs = {"min": b} if (self.fn is max) else {"max": b}
                result = fn.call_function(tx, [a], kwargs)
            else:
                if isinstance(a, variables.NumpyNdarrayVariable):
                    import numpy as np

                    np_fn = {max: np.maximum, min: np.minimum}[self.fn]
                    fn = variables.NumpyVariable(np_fn)
                else:
                    torch_fn = {max: torch.maximum, min: torch.minimum}[self.fn]
                    fn = variables.TorchInGraphFunctionVariable(torch_fn)
                result = fn.call_function(tx, [a, b], {})

            # return unspec if both a, b are unspec or const
            if all(
                isinstance(
                    i,
                    (
                        variables.UnspecializedPythonVariable,
                        variables.ConstantVariable,
                    ),
                )
                for i in [a, b]
            ):
                if any(isinstance(val, FakeItemVariable) for val in [a, b]):
                    # type: ignore[arg-type]
                    return variables.FakeItemVariable.from_tensor_variable(result)

                if b.is_python_constant():
                    raw_b = b.as_python_constant()
                else:
                    raw_b = b.raw_value  # type: ignore[attr-defined]
                if self.fn is max:
                    raw_res = max(a.raw_value, raw_b)  # type: ignore[attr-defined]
                else:
                    raw_res = min(a.raw_value, raw_b)  # type: ignore[attr-defined]

                need_unwrap = any(
                    x.need_unwrap
                    for x in [a, b]
                    if isinstance(x, variables.UnspecializedPythonVariable)
                )
                return variables.UnspecializedPythonVariable.from_tensor_variable(
                    result,  # type: ignore[arg-type]
                    raw_res,
                    need_unwrap,
                )
            # otherwise return tensor
            else:
                return result
        elif isinstance(a, SymNodeVariable) or isinstance(b, SymNodeVariable):
            py_fn = torch.sym_max if self.fn is max else torch.sym_min
            proxy = tx.output.create_proxy(
                "call_function", py_fn, *proxy_args_kwargs([a, b], {})
            )
            return SymNodeVariable.create(tx, proxy, None)
        elif isinstance(a, ConstantVariable) and isinstance(b, ConstantVariable):
            value = self.fn(
                a.as_python_constant(),
                b.as_python_constant(),
            )
            return VariableTracker.build(tx, value)
        return None