def call_function(
        self,
        tx: "InstructionTranslator",
        args: Sequence[VariableTracker],
        kwargs: dict[str, VariableTracker],
    ) -> VariableTracker:
        # importlib functions are frozen builtins that Dynamo cannot trace
        # into.  They are deterministic for a given package name, so
        # constant-fold them when all args are constants.
        if self.value in (importlib.util.find_spec, importlib.metadata.version) and all(
            a.is_python_constant() for a in args
        ):
            return VariableTracker.build(
                tx, self.value(*(a.as_python_constant() for a in args))
            )

        if inspect.getattr_static(self.value, "_torchdynamo_disable", False):
            msg = inspect.getattr_static(self.value, "_torchdynamo_disable_msg", None)
            unimplemented(
                gb_type="Skip calling `torch.compiler.disable()`d function",
                context=str(self.value),
                explanation=f"Skip calling function `{self.value}` since it was wrapped "
                f"with `torch.compiler.disable` (reason: {msg})",
                hints=[
                    "Remove the `torch.compiler.disable` call",
                ],
            )
        elif self.value is torch._dynamo.graph_break:
            graph_break_msg = kwargs.get("msg")
            if graph_break_msg:
                graph_break_msg = graph_break_msg.as_python_constant()
            unimplemented(
                gb_type="Call to `torch._dynamo.graph_break()`",
                context=f"Called `torch._dynamo.graph_break()` with args `{args}`, kwargs `{kwargs}`",
                explanation=f"User-inserted graph break. Message: {graph_break_msg}",
                hints=[
                    "Remove the `torch._dynamo.graph_break()` call.",
                ],
            )
        elif self.value is torch._dynamo.skip_frame:
            skip_frame_msg = kwargs.get("msg")
            if skip_frame_msg:
                skip_frame_msg = skip_frame_msg.as_python_constant()
            else:
                skip_frame_msg = ""
            unimplemented(
                gb_type="Call to `torch._dynamo.skip_frame()`",
                context=f"Called `torch._dynamo.skip_frame()` with args `{args}`, kwargs `{kwargs}`. "
                f"Skipping frame {format_frame_info(tx.f_code)}.",
                explanation=f"User-inserted skip frame. Message: {skip_frame_msg}",
                hints=[
                    "Remove the `torch._dynamo.skip_frame()` call.",
                ],
                skip_frame=True,
            )
        elif self.value is torch._dynamo.step_unsupported:
            try:
                unimplemented(
                    gb_type="Call to `torch._dynamo.step_unsupported()`",
                    context="",
                    explanation="User-inserted step_unsupported.",
                    hints=[
                        "Remove the `torch._dynamo.step_unsupported()` call.",
                    ],
                )
            except Unsupported as e:
                raise StepUnsupported(e.msg) from None
        elif self.value is types.FunctionType.__get__:
            # function.__get__(func, obj[, cls]) produces a bound method.
            # This is called by inspect._descriptor_get when resolving
            # descriptors during inspect.signature().
            # Note that function.__get__ does not use the 3rd argument. The
            # reason it still has the 3rd argument is because descriptors follow
            # a function signature that takes 3 arguments, and other descriptors
            # (not function.__get__) can use the 3rd argument.
            if len(args) in (2, 3) and not kwargs:
                func_var = args[0]
                obj_var = args[1]
                if isinstance(func_var, UserFunctionVariable):
                    return UserMethodVariable(
                        func_var.fn, obj_var, source_fn=func_var.source
                    )
            unimplemented(
                gb_type="unsupported function.__get__ call",
                context=f"call_function {self}, args: {args}, kwargs: {kwargs}",
                explanation="Dynamo only supports function.__get__(func, obj[, cls]) "
                "where func is a user-defined function.",
                hints=[*graph_break_hints.SUPPORTABLE],
            )
        else:
            if config.dont_skip_tracing:
                from .builder import SourcelessBuilder

                # re-build the function, attempting to not skip
                rebuilt_fn = SourcelessBuilder.create(tx, self.value)
                # if we still get SkipFunctionVariable, then we *really* should skip this function
                if not isinstance(rebuilt_fn, SkipFunctionVariable):
                    return rebuilt_fn.call_function(tx, args, kwargs)
            qualname = getattr(self.value, "__qualname__", "<unknown qualname>")
            module_or = getattr(self.value, "__module__", None)
            module_name = "<unknown module>" if module_or is None else str(module_or)
            try:
                path = inspect.getfile(self.value)
                explanation = (
                    f"Dynamo developers have intentionally marked that the function `{qualname}` "
                    f"in file `{path}` should not be traced."
                )
                hints = [
                    f"Avoid calling the function `{qualname}`.",
                ]
                # TODO improve trace_rules reasoning to provide better hints.
                # How do we tell that a function/file should NOT be removed from skip files?
                # Do a very basic check for now.
                if "_dynamo" not in path:
                    hints += [
                        f"Apply `@torch._dynamo.dont_skip_tracing` to the function `{qualname}` "
                        "to force tracing into the function. "
                        "More graph breaks may occur as a result of attempting to trace into the function.",
                        "Please file an issue to PyTorch.",
                    ]
            except TypeError:
                known_python_builtin_modules = {"_abc", "_warnings"}
                if module_or in known_python_builtin_modules:
                    explanation = (
                        f"Dynamo does not know how to trace the Python builtin "
                        f"`{module_name}.{qualname}`."
                    )
                    hints = [
                        "If you are attempting to call a logging function (e.g. `_warnings.warn`), "
                        "you can try adding it to `torch._dynamo.config.reorderable_logging_functions`.",
                        "Please file an issue on GitHub "
                        "so the PyTorch team can add support for it. ",
                    ]
                elif module_or is not None and module_or.startswith("optree"):
                    explanation = f"Dynamo cannot trace optree C/C++ function {module_name}.{qualname}."
                    hints = [
                        " Consider using torch.utils._pytree - "
                        "https://github.com/pytorch/pytorch/blob/main/torch/utils/_pytree.py"
                    ]
                    # also warn on it because most users won't see the graph break message
                    torch._dynamo.utils.warn_once(explanation + "\n" + "\n".join(hints))
                else:
                    explanation = (
                        f"Dynamo does not know how to trace the builtin `{module_name}.{qualname}.` "
                        f"This function is either a Python builtin (e.g. _warnings.warn) "
                        f"or a third-party C/C++ Python extension (perhaps created with pybind)."
                    )
                    hints = [
                        "If it is a Python builtin, please file an issue on GitHub "
                        "so the PyTorch team can add support for it and see the next case for a workaround.",
                        "If it is a third-party C/C++ Python extension, please "
                        "either wrap it into a PyTorch-understood custom operator "
                        "(see https://pytorch.org/tutorials/advanced/custom_ops_landing_page.html "
                        "for more details) or, if it is traceable, use "
                        "`torch.compiler.allow_in_graph`.",
                    ]
                    # also warn on it because most users won't see the graph break message
                    torch._dynamo.utils.warn_once(explanation + "\n" + "\n".join(hints))
            if qualname == "allow_in_graph":
                explanation = (
                    "torch.compiler.allow_in_graph (or torch._dynamo.allow_in_graph) "
                    "was called inside a compiled region. Dynamically annotating functions "
                    "inside a compiled region is not supported."
                )
                hints = [
                    "Apply @torch.compiler.allow_in_graph as a decorator before compilation, "
                    "not inside the compiled function.",
                ]
            if self.reason:
                reason = self.reason
            else:
                from ..trace_rules import get_skip_reason

                reason = get_skip_reason(self.value)
            unimplemented(
                gb_type="Attempted to call function marked as skipped",
                context=f"module: {module_name}, qualname: {qualname}, skip reason: {reason}",
                explanation=explanation,
                hints=hints,
            )