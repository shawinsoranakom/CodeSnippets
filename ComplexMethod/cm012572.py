def _bound_variable(self, name: str, *args: Any, **kwargs: Any) -> ValueRanges[Any]:
        """
        If the variable comes from an FX node, we forward the bound we have already computed
        Else, if the variable when codegen'ing another op, we try to compute its bounds
        """
        from ..bounds import ValueRangeAnalysis
        from ..select_algorithm import TritonTemplateKernel
        from .cutlass.kernel import CUTLASSTemplateKernel

        if isinstance(V.kernel, TritonTemplateKernel):
            return ValueRanges.unknown()

        if isinstance(V.kernel, CUTLASSTemplateKernel):
            return ValueRanges.unknown()

        if isinstance(V.interpreter, NullHandler):
            return ValueRanges.unknown()

        fx_node = V.interpreter.current_node
        if fx_node.target == name and self.kernel.node_to_bounds is not None:
            assert isinstance(self.kernel.node_to_bounds, dict), type(
                self.kernel.node_to_bounds
            )
            return self.kernel.node_to_bounds.get(fx_node, ValueRanges.unknown())
        elif config.compute_all_bounds and hasattr(ValueRangeAnalysis, name):
            # These create lots of inner strings. We would need to compute the bounds at the ops
            # We will also likely not get much from computing VRs on these nodes
            if any(s in fx_node.target for s in ("set_indirect", "reduction", "scan")):
                return ValueRanges.unknown()

            # We assume that the inputs come from `ops.` and are not strings. If you want to generate
            # intermediary strings, wrap them in CSE variables with properly initialised bounds.

            # If there is no FX bound but we know how to compute one we do so
            assert not kwargs

            def arg_to_bound(x: Any) -> Any:
                if isinstance(x, CSEVariable):
                    return x.bounds
                elif isinstance(x, sympy.Expr):
                    return bound_sympy(x)
                else:
                    return x

            arg_bounds = list(map(arg_to_bound, args))
            return getattr(self.vr_analysis, name)(*arg_bounds)
        return ValueRanges.unknown()