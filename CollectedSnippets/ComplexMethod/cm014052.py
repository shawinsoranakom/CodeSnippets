def __call__(
        self, value: VariableTracker | Source | None, allow_cache: bool = True
    ) -> None:
        """
        Generate code such that top-of-stack (TOS) is set to value.

        `allow_cache` controls the behavior in the following manner. `value` can
        either be a VariableTracker or a Source.

        If `value` is a `Source`, `allow_cache` must be True (invariant asserted
        below). If the source was reconstructed earlier, we will reuse the
        generated code by loading from top of stack or tempvars.

        If `value` is a `VariableTracker`, we have the following cases:

        1) `allow_cache=True`
            a) If the value.source is not None, we will emit the code based on
            `value.source` to handle aliasing.
            b) If value.source is None (example reconstructing a local list
            returned by the compiled function), we will reconstruct the variable
            tracker (w/o any source) to emit bytecode that generates a new
            python object.

            In both cases of value.source being None or not, if the value was
            reconstructed earlier, we will reuse the generated code by loading from
            top of stack or tempvars.

        2) `allow_cache=False` - This is a special case (allow_cache defaults to
        True).
            a) If the value.source is not None, we reconstruct the variable
            tracker and emit a new python object. You might wonder what about
            aliasing? The place where we use this config also has the followup
            code where the original python object is assigned to this new python
            value to handle aliasing (check side_effects.py and search for
            allow_cache=False).

            b) If value.source is None, this is not allowed

        Notable effects:
        1. `self.top_of_stack` will be set to `value`, if we don't codegen
           `value` based on source.
        2. `self.uses[value]` will increment, unless (a). we codegen via
            `top_of_stack` or cached `tempvars`, or (b). `value` has special VT
            types like `NNModuleVariable`, etc.
        """
        assert value is not None
        if isinstance(value, Source):
            # If the source needs to be overridden, use the new one.
            source = self.overridden_sources.get(value, value)
            assert allow_cache is True, "allow_cache must be True for Source"
            if self.top_of_stack is value:
                self._output.append(create_dup_top())
                return

            if self.tempvars.get(source) is not None:
                self._output.append(self.create_load(self.tempvars[source]))
                self.top_of_stack = source
                return

            self.uses[source] += 1
            try:
                self.call_reconstruct(source)
            except NotImplementedError:
                unimplemented(
                    gb_type="Reconstruction failure: source.reconstruct not implemented",
                    context=str(source),
                    explanation=f"Dynamo has no bytecode reconstruction implemented for {type(source)} variable {source}.",
                    hints=[*graph_break_hints.DYNAMO_BUG],
                )
            if source in self.tempvars:
                self._output.append(create_dup_top())
                self.add_cache(source)
            self.top_of_stack = source

            return

        assert isinstance(value, VariableTracker)
        output = self._output
        graph_outputs = self.graph_outputs

        if allow_cache:
            if self.top_of_stack is value:
                output.append(create_dup_top())
                return

            if self.tempvars.get(value) is not None:
                output.append(self.create_load(self.tempvars[value]))
                self.top_of_stack = value
                return

        if value.is_realized() and isinstance(
            value, ContextlibContextManagerLocalGeneratorObjectVariable
        ):
            unimplemented(
                gb_type="reconstructing @contextmanager object",
                context=f"object: {value}",
                explanation="Returning a @contextmanager object from a compiled function is not supported.",
                hints=[
                    *graph_break_hints.SUPPORTABLE,
                ],
            )

        # Dynamo normally prefers codegen from source to account for aliasing.
        if (
            value.source is not None
            and allow_cache
            and not (
                value.is_realized() and isinstance(value, LocalGeneratorObjectVariable)
            )
        ):
            # There's a corner case for export: for instance, if the computation
            # graph is just identity on an input tensor, Dynamo would just emit
            # a `LOAD_FAST` from the input source, rather than generating an
            # identity FX graph.
            #
            # However, export wants to maximize graph capture; in the case
            # above, export _wants to_ obtain an identity FX graph (despite it
            # appears unnecessarily expensive for `torch.compile`), so we have
            # the following option to override Dynamo's preference for codegen
            # from source. Moreover, this option applies recursively, for cases
            # like input tensor being returned in a new dictionary.
            #
            # And why the `ValueMutationExisting` check? Not sure, so leaving it
            # to keep the old behavior, as when `value_from_source` was
            # introduced. TODO sort out the invariants among side effect,
            # codegen and export.
            if (
                isinstance(value.mutation_type, ValueMutationExisting)
                or self.value_from_source
            ):
                return self(value.source)

        if value.is_python_constant() and is_safe_constant(value.as_python_constant()):
            output.append(self.create_load_const(value.as_python_constant()))
        elif isinstance(value, TensorWithTFOverrideVariable):
            graph_outputs_key = self.add_graph_output(value)

            self.add_push_null(
                lambda: self.load_import_from(utils.__name__, "to_subclass")
            )
            self.load_graph_output(graph_outputs[graph_outputs_key].index)
            output.append(
                self.create_load_global(
                    value.global_mangled_class_name(self.tx),  # type: ignore[arg-type]
                    add=True,
                )
            )
            output.extend(create_call_function(2, False))
        elif (
            isinstance(value, SymNodeVariable)
            and value.python_type() is float
            and not self.tx.export
        ):
            # This is a little unusual; force the output convention to be a
            # Tensor here.  Don't do this for export because this is
            # apparently load bearing for export tests (but I am a bit
            # doubtful it actually works in the real world)
            # NB: It works to add_graph_output on a computed expression
            # as_tensor here, because we memoize as_tensor calls on
            # SymNodeVariable!
            graph_outputs_key = self.add_graph_output(
                value.as_tensor(self.tx, torch.float64)
            )

            def gen_fn() -> None:
                self.load_graph_output(graph_outputs[graph_outputs_key].index)
                output.append(self.create_load_attr("item"))

            self.add_push_null(gen_fn)
            output.extend(create_call_function(0, False))
        elif isinstance(
            value,
            (
                TensorVariable,
                SymNodeVariable,
                UnspecializedPythonVariable,
                NumpyNdarrayVariable,
                TorchScriptObjectVariable,
            ),
        ):
            graph_outputs_key = self.add_graph_output(value)

            if isinstance(value, NumpyNdarrayVariable):
                self.add_push_null(
                    lambda: self.load_import_from(utils.__name__, "to_numpy_helper")
                )
                self.load_graph_output(graph_outputs[graph_outputs_key].index)
                output.extend(create_call_function(1, False))
            elif isinstance(value, UnspecializedPythonVariable) and value.need_unwrap:

                def gen_fn() -> None:
                    self.load_graph_output(graph_outputs[graph_outputs_key].index)
                    output.append(self.create_load_attr("item"))

                self.add_push_null(gen_fn)
                output.extend(create_call_function(0, False))
            else:
                self.load_graph_output(graph_outputs[graph_outputs_key].index)
        elif isinstance(value, NNModuleVariable):
            parts = value.module_key.split(".")
            if parts[0] in self.code_options["co_varnames"]:
                output.append(self.create_load(parts[0]))
                parts = parts[1:]
            else:
                assert self.root is not None
                output.append(self.create_load_const_unchecked(self.root))
            for part in parts:
                output.append(self.create_load_attr(part))
        else:
            self.uses[value] += 1
            try:
                self.call_reconstruct(value)
            except NotImplementedError as e:
                unimplemented(
                    gb_type="Reconstruction failure",
                    context=str(value),
                    explanation=f"Dynamo has no bytecode reconstruction implemented for sourceless variable {value}.",
                    hints=[
                        "If Dynamo is attempting to trace a return statement and your code is attempting to return a variable "
                        "that Dynamo cannot reconstruct, then remove it from the return statement.",
                        *graph_break_hints.CAUSED_BY_EARLIER_GRAPH_BREAK,
                        "Report an issue to PyTorch if you need reconstrtuction support. Note that objects that don't have "
                        "reconstruction rules may be fundamentally unreconstructable.",
                    ],
                    from_exc=e,
                )
            if allow_cache and value in self.tempvars:
                self._output.append(create_dup_top())
                self.add_cache(value)

        self.top_of_stack = value