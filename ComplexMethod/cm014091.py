def call_function(
        self,
        tx: "InstructionTranslator",
        args: Sequence[VariableTracker],
        kwargs: dict[str, VariableTracker],
    ) -> VariableTracker:
        # NOTE this is to handle methods annotated by `nonstrict_trace`.
        # a `nonstrict_trace`-ed function will be wrapped by
        # `VariableTracker.build` and route to `TorchInGraphFunctionVariable`,
        # but in the case of method, we manually wrap it with `UserMethodVariable`
        # inside `UserDefinedObjectVariable.var_getattr`.
        #
        # We might be able to simplify this away by canonicalizing the
        # function/method wrapping code paths.
        from ..trace_rules import is_leaf_function, is_nonstrict_trace_callable

        if is_nonstrict_trace_callable(self.fn):
            call_args = [*self.self_args(), *args]
            var = variables.TorchInGraphFunctionVariable(
                self.fn, kind=variables.torch.AllowInGraphKind.NONSTRICT_TRACE
            )
            return var.call_function(tx, call_args, kwargs)

        if is_leaf_function(self.fn):
            call_args = [*self.self_args(), *args]
            var = variables.TorchInGraphFunctionVariable(
                self.fn, kind=variables.torch.AllowInGraphKind.LEAF_FUNCTION
            )
            return var.call_function(tx, call_args, kwargs)

        # For nn.Module methods, redirecting to NNModuleVariable.call_method for optimized solution
        # rather than simple inlining. E.g, putting `call_method` op in FX graph for `forward` method
        # since we ensure `forward` of allowed modules can be traced by AOT safely.
        # Note this is not only for allowed modules, as user customized modules can extend from
        # allowed modules but using parent's `forward` method, which is also covered by this branch.

        # If we are tracing the higher order op, we want Dynamo to step inside
        # the module call so that Dynamo can see the underlying parameters and
        # buffers and raise them as inputs to the graph. The is_root_tracer
        # check bypasses the if condition for non-root tracers and directly
        # calls the super().call_function at the end, which is basically
        # equivalent of inlining the method.
        if tx.output.is_root_tracer() and isinstance(
            self.obj, variables.NNModuleVariable
        ):
            module_attr = getattr(self.fn, "__module__", "")
            # inline torch.nn.utils.parametrize
            if (
                module_attr is not None
                and module_attr.startswith("torch.nn.")
                and module_attr != "torch.nn.utils.parametrize"
                or self.is_constant
            ):
                return self.obj.call_method(
                    tx, self.fn.__name__, list(args), kwargs, constant=self.is_constant
                )
        elif (
            _fsdp_param_group is not None
            and self.fn is _fsdp_param_group.FSDPParamGroup.use_training_state  # type: ignore[attr-defined]
        ):
            return variables.TorchCtxManagerClassVariable(self.fn).call_function(
                tx, (self.obj, *args), kwargs
            )
        if self.is_constant:
            fn = getattr(self.obj.value, self.fn.__name__)  # type: ignore[attr-defined]
            return invoke_and_store_as_constant(tx, fn, self.get_name(), args, kwargs)
        return super().call_function(tx, args, kwargs)