def call_method(
        self,
        tx: "InstructionTranslator",
        name: str,
        args: list[Any],
        kwargs: dict[str, Any],
    ) -> VariableTracker:
        from .. import trace_rules
        from . import UserMethodVariable
        from .constant import ConstantVariable

        method = self._maybe_get_baseclass_method(name)
        if method is not None:
            if method is object.__init__:
                return ConstantVariable.create(None)

            if is_standard_setattr(method) or isinstance(self.value, threading.local):
                return self.method_setattr_standard(tx, *args, **kwargs)

            if is_standard_delattr(method):
                return self.method_setattr_standard(
                    tx, args[0], variables.DeletedVariable()
                )

            if method is object.__eq__ and len(args) == 1 and not kwargs:
                other = args[0]
                if not isinstance(other, UserDefinedObjectVariable):
                    return VariableTracker.build(tx, NotImplemented)

                # TODO(anijain2305) - Identity checking should already be a part
                # of the cmp_eq  polyfill function.
                return VariableTracker.build(tx, self.value is other.value)

            if torch._dynamo.config.enable_faithful_generator_behavior and isinstance(
                self.value, types.GeneratorType
            ):
                unimplemented(
                    gb_type="call_method on generator",
                    context=f"object={self.value}, method={name}, args={args}, kwargs={kwargs}",
                    explanation="Detected a method call to a user-defined generator object. "
                    "This is not fully supported.",
                    hints=[
                        "Set `torch._dynamo.config.enable_faithful_generator_behavior = False`. Note that this "
                        "may cause silent incorrectness, since we will eagerly unpack generators instead of lazily "
                        "evaluating them.",
                    ],
                )

            # torch.Generator methods like manual_seed(), get_state(), etc.
            # are stateful RNG operations that cannot be soundly traced.
            if (
                isinstance(self.value, torch._C.Generator)
                and name in trace_rules._GENERATOR_METHODS_THAT_GRAPH_BREAK
            ):
                unimplemented(
                    gb_type="torch.Generator method",
                    context=f"torch.Generator.{name}",
                    explanation=f"torch.Generator.{name}() is a stateful RNG "
                    "operation that cannot be soundly traced in the FX graph.",
                    hints=[*graph_break_hints.FUNDAMENTAL],
                )

            # Delegate to _base_vt for non-overridden base-class methods
            if (
                self._base_vt is not None
                and self._base_methods is not None
                and method in self._base_methods
            ):
                return self._base_vt.call_method(tx, name, args, kwargs)

            # check for methods implemented in C++
            if isinstance(method, types.FunctionType):
                source = self.source
                source_fn = None
                if source:
                    source_fn = self.get_source_by_walking_mro(tx, name)
                # TODO(jansel): add a guard to check for monkey patching?
                from ..mutation_guard import unpatched_nn_module_init

                if method is torch.nn.Module.__init__:
                    method = unpatched_nn_module_init
                return UserMethodVariable(
                    method, self, source_fn=source_fn, source=source
                ).call_function(tx, args, kwargs)  # type: ignore[arg-type]

            if method is list.__len__ and self.source and not (args or kwargs):
                install_guard(self.source.make_guard(GuardBuilder.SEQUENCE_LENGTH))
                return VariableTracker.build(tx, len(self.value))  # type: ignore[arg-type]

        return super().call_method(tx, name, args, kwargs)