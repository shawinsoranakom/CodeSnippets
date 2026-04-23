def call_function(
        self,
        tx: "InstructionTranslator",
        args: Sequence[VariableTracker],
        kwargs: dict[str, VariableTracker],
    ) -> VariableTracker:
        # Handle patch_dynamo_config call
        if self.fn is torch._dynamo.patch_dynamo_config:
            try:
                args_const = [arg.as_python_constant() for arg in args]
                kwargs_const = {
                    key: val.as_python_constant() for key, val in kwargs.items()
                }
                changes = torch._dynamo.patch_dynamo_config(
                    *args_const, **kwargs_const
                ).changes
                return variables.DynamoConfigPatchVariable(changes)
            except AsPythonConstantNotImplementedError as e:
                raise RuntimeError(
                    "Cannot convert patch_dynamo_config args/kwargs to constants. "
                    "Please fix your call to patch_dynamo_config by using simpler inputs. "
                    f"args: {args}, kwargs: {kwargs}"
                ) from e
        elif self.fn is torch._dynamo.error_on_graph_break:
            try:
                bound = inspect.signature(self.fn).bind(*args, **kwargs)
                error_on_graph_break = bound.arguments[
                    "error_on_graph_break"
                ].as_python_constant()
                assert isinstance(error_on_graph_break, bool)
                return variables.ErrorOnGraphBreakVariable(error_on_graph_break)
            except Exception as e:
                raise RuntimeError(
                    "Improper error_on_graph_break() call. Please fix your call to error_on_graph_break(). "
                    f"args: {args}, kwargs: {kwargs}"
                ) from e
        elif self.fn is torch._dynamo.override_cudagraphs:
            try:
                bound = inspect.signature(self.fn).bind(*args, **kwargs)
                bound.apply_defaults()
                fwd = bound.arguments["fwd"]
                bwd = bound.arguments["bwd"]
                if isinstance(fwd, VariableTracker):
                    fwd = fwd.as_python_constant()
                if isinstance(bwd, VariableTracker):
                    bwd = bwd.as_python_constant()
                return variables.CudagraphOverrideVariable(fwd, bwd)
            except Exception as e:
                raise RuntimeError(
                    "Improper override_cudagraphs() call. Please fix your call to override_cudagraphs(). "
                    f"args: {args}, kwargs: {kwargs}"
                ) from e
        elif self.fn is torch._dynamo.bytecode_debugger.breakpoint:
            tx.output._emit_debugger_breakpoint = True
            return variables.ConstantVariable.create(None)
        # Handle a `nonstrict_trace(fn)` call
        elif self.fn is torch._dynamo.nonstrict_trace:
            bound = inspect.signature(self.fn).bind(*args, **kwargs)
            fn_var = bound.args[0]
            if not isinstance(fn_var, BaseUserFunctionVariable):
                typ = fn_var.python_type()
                msg = f"`nonstrict_trace` expects a callable, but got value of type <{typ.__name__}>"
                unimplemented(
                    gb_type="TypeError from user code",
                    context=f"call_function({self.value}, {args}, {kwargs})",  # type: ignore[attr-defined]
                    explanation=msg,
                    hints=[
                        *graph_break_hints.USER_ERROR,
                    ],
                )

            if not isinstance(fn_var, UserFunctionVariable):
                fn_name = fn_var.get_name()
                msg = f"Applying `nonstrict_trace` to function <{fn_name}>; however, `nonstrict_trace` currently requires the function to be defined outside `torch.compile` region."
                unimplemented(
                    gb_type="Limitation of `nonstrict_trace",
                    context=f"{self}",
                    explanation=msg,
                    hints=[
                        f"make sure definition of {fn_name} is outside ",
                        "`torch.compile` region",
                    ],
                )

            fn = fn_var.fn
            return variables.TorchInGraphFunctionVariable(
                fn, kind=variables.torch.AllowInGraphKind.NONSTRICT_TRACE
            )

        if self.is_constant:
            return invoke_and_store_as_constant(
                tx, self.fn, self.get_name(), args, kwargs
            )

        if (
            not tx.output.current_tracer.unsafe_allow_externally_visible_side_effects
            and self.fn
            is torch._dynamo.utils._disable_side_effect_safety_checks_for_current_subtracer
        ):
            with torch._dynamo.side_effects.allow_externally_visible_side_effects_in_subtracer(
                tx
            ):
                return super().call_function(tx, args, kwargs)

        if (
            getattr(tx.output.current_tracer, "description", None)
            == "torch.utils.checkpoint.checkpoint"
            and not tx.output.current_tracer.allow_side_effects_in_hop
        ):
            try:
                from torch.distributed.fsdp._fully_shard._fsdp_state import FSDPState
            except Exception:
                FSDPState = None  # type: ignore[assignment, misc]
            if FSDPState is not None and self.fn in [
                FSDPState._pre_forward,
                FSDPState._post_forward,
            ]:
                with torch._dynamo.side_effects.allow_side_effects_in_hop(tx):
                    return super().call_function(tx, args, kwargs)

        tree_map_result = self._maybe_call_tree_map_fastpath(tx, args, kwargs)
        if tree_map_result is not None:
            return tree_map_result

        return super().call_function(tx, args, kwargs)