def call_method(
        self,
        tx: "InstructionTranslator",
        name: str,
        args: Sequence[VariableTracker],
        kwargs: dict[str, VariableTracker],
    ) -> VariableTracker:
        if name in ["_call_impl", "_wrapped_call_impl"]:
            fn = getattr(self.value_type, name)
            if self.source:
                source = self.get_source_by_walking_mro(tx, name)
            else:
                source = None

            fn_vt = VariableTracker.build(tx, fn, source=source, realize=True)
            return fn_vt.call_function(tx, [self] + list(args), kwargs)

        if not self.has_key_in_generic_dict(tx, name):
            try:
                method = inspect.getattr_static(type(self.value), name)
            except AttributeError:
                method = None

            if isinstance(method, staticmethod):
                source = AttrSource(
                    self.get_source_by_walking_mro(tx, name), "__func__"
                )
                fn_vt = VariableTracker.build(
                    tx, method.__func__, source=source, realize=True
                )
                return fn_vt.call_function(tx, args, kwargs)

            if (
                hasattr(method, "__code__")
                and id(method.__code__) in self._nn_module_method_ids()
            ):
                unimplemented(
                    gb_type="UnspecializedNNModuleVariable missing method",
                    context=f"call_method: {self} {name} {args} {kwargs}",
                    explanation=f"Dynamo does not support tracing method {name} of nn.Module {self.value}",
                    hints=[
                        "Dynamo does not really define unspecialized nn.Module very well.",
                        *graph_break_hints.DIFFICULT,
                    ],
                )

            # "_parameters" in self.value.__dict__ checks that module is initialized
            if name == "__setattr__" and "_parameters" in self.value.__dict__:
                # Record if mutations happens on parameters/buffers/modules. The
                # mutations on these are not tracked by base class
                # UserDefinedObject vt. This will be used later to graph break
                # on seeing a parameters() and family calls.
                # TODO(anijain2305) - This might not be needed if we let Dynamo
                # inline both getattr and setattr. In that case, it should see
                # the lowest level dicts - _parameters and family and
                # automatically track mutations on those. Investigate if that
                # can be done.
                attr_name = args[0].as_python_constant()
                value = args[1]

                # This is reverse engineered by looking at nn module __setattr__
                # logic.
                if (
                    value.is_tensor() and value.python_type() is torch.nn.Parameter
                ) or attr_name in self.value.__dict__["_parameters"]:
                    # Handle parameters
                    self.is_state_mutated = True
                elif attr_name in self.value.__dict__["_buffers"]:
                    # Handle buffers
                    self.is_state_mutated = True
                elif (
                    isinstance(
                        value,
                        (
                            variables.NNModuleVariable,
                            variables.UnspecializedNNModuleVariable,
                        ),
                    )
                    or attr_name in self.value.__dict__["_modules"]
                ):
                    # Handle submodules
                    self.is_state_mutated = True

            if (
                method is torch.nn.Module.__setattr__
                and isinstance(args[1], variables.DeletedVariable)
            ) or method is torch.nn.Module.__delattr__:
                # Trace through __delattr__ to track mutations on the module
                # members like `_modules``.
                fn_vt = VariableTracker.build(tx, torch.nn.Module.__delattr__)
                return fn_vt.call_function(tx, [self, args[0]], kwargs)

        return super().call_method(tx, name, list(args), kwargs)