def handle_constant_processgroup_functions(
                self,
                tx: "InstructionTranslator",
                *args: VariableTracker,
                **kwargs: VariableTracker,
            ) -> VariableTracker:
                # We desugar it at trace-time into ranks by directly calling util
                # bake the result into the trace
                if len(args) == 0 and len(kwargs) == 0:
                    # get_rank() or get_world_size() with no args (uses default group)
                    pass
                elif len(args) == 1 and len(kwargs) == 0:
                    # group or group name
                    assert args[0].is_python_constant() or (
                        isinstance(args[0], TorchScriptObjectVariable)
                        and args[  # pyrefly: ignore[missing-attribute]
                            0
                        ].value.script_class_name  # pyrefly: ignore[missing-attribute]
                        == "torch.distributed.distributed_c10d.ProcessGroup"
                    )
                elif len(args) == 2 and len(kwargs) == 0:
                    # ranks + tag
                    assert (
                        isinstance(args[0], ListVariable)
                        and args[1].is_python_constant()
                    )
                elif len(args) == 0 and len(kwargs) > 0:
                    # All keyword arguments (e.g., get_world_size(group=...))
                    pass
                else:
                    raise AssertionError(
                        f"Invalid group value ({args}, {kwargs}) for constant pg "
                        f"function {self.value}"
                    )

                def get_arg_value(arg: VariableTracker) -> Any:
                    # TorchScriptObjectVariable for ProcessGroup doesn't support
                    # as_python_constant(), so extract real_obj directly
                    if isinstance(arg, TorchScriptObjectVariable):
                        return arg.value.real_obj  # pyrefly: ignore[missing-attribute]
                    return arg.as_python_constant()

                args_as_value = [get_arg_value(arg) for arg in args]
                kwargs_as_value = {k: get_arg_value(v) for k, v in kwargs.items()}
                invocation_result = self.value(*args_as_value, **kwargs_as_value)

                # Note - while we *could* cook up sources around invocations, like a FunctionSource
                # the space of invoking functions in the middle of the guard chain is very iffy. As such,
                # guard propagation via options is the best we can do.
                return VariableTracker.build(tx, invocation_result)