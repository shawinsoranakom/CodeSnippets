def generic_getattr(
        self, tx: "InstructionTranslator", name: str
    ) -> VariableTracker:
        """Dynamo implementation of CPython's PyObject_GenericGetAttr.

        This mirrors object.__getattribute__ and is called from:
        - var_getattr (for objects without a custom __getattribute__)
        - SuperVariable.call_method (when super().__getattribute__() resolves
          to object.__getattribute__)

        The algorithm: MRO walk → data descriptor → instance __dict__ →
        non-data descriptor / plain class attr → dynamic fallback →
        __getattr__ → AttributeError.
        """
        source: Source | None = AttrSource(self.source, name) if self.source else None

        if tx.output.side_effects.has_pending_mutation_of_attr(self, name):
            result = tx.output.side_effects.load_attr(self, name, deleted_ok=True)
            if isinstance(result, variables.DeletedVariable):
                raise_observed_exception(
                    AttributeError,
                    tx,
                    args=[
                        f"'{type(self.value).__name__}' object has no attribute '{name}'",
                    ],
                )
            return result

        if name == "__dict__":
            if not hasattr(self.value, "__dict__"):
                raise_observed_exception(AttributeError, tx)
            return self.get_dict_vt(tx)

        # TODO(anijain2305) - Investigate if we need specialization for more
        # dunder attrs. inspect.getattr_static does not return correct value for
        # them.
        if name == "__class__":
            cls_source: Source | None = source
            if source is None:
                cls_source = self.cls_source
            else:
                cls_source = source
            return VariableTracker.build(tx, type(self.value), cls_source)

        from ..mutation_guard import unpatched_nn_module_init

        # ---- CPython attribute lookup algorithm ----
        # Mirror object.__getattribute__ (PyObject_GenericGetAttr):
        #   1. type_attr = lookup name in type(obj).__mro__
        #   2. if type_attr is a DATA descriptor → invoke it
        #   3. if name in obj.__dict__ → return as-is (no descriptor invocation)
        #   4. if type_attr is a non-data descriptor → invoke it
        #   5. if type_attr is a plain class variable → return it
        #   6. __getattr__ fallback
        #   7. raise AttributeError
        #
        # Between steps 5 and 6, we also handle objects with custom storage
        # that aren't visible via the MRO walk or instance __dict__ (step 5b).
        #
        # Step 1: Single MRO walk on the type (cached).
        type_attr = self.lookup_class_mro_attr(name)

        # Dynamo patches nn.Module.__init__ at import time to inject tracing
        # hooks.  Undo that here so the unpatched original is traced instead.
        if type_attr is torch.nn.Module.__init__:
            type_attr = unpatched_nn_module_init

        # Step 2: Data descriptors on the type take priority over instance dict.
        if type_attr is not NO_SUCH_SUBOBJ and is_data_descriptor(type_attr):
            return self.resolve_data_descriptor(tx, name, type_attr, source)

        # Step 3: Instance __dict__ — return as-is, no descriptor invocation.
        # TODO(guilhermeleobas): step 3 should look into dict_vt and not self.value.__dict__
        # as the object could have mutated an attribute via setattr
        if hasattr(self.value, "__dict__") and name in self.value.__dict__:
            subobj = self.value.__dict__[name]
            source = self.maybe_wrap_nn_module_source_for_instance(tx, name, source)
            return VariableTracker.build(tx, subobj, source)

        # Step 4-5: Non-data descriptor or plain class attribute.
        if type_attr is not NO_SUCH_SUBOBJ:
            return self.resolve_type_attr(tx, name, type_attr, source)

        # Step 5b: Dynamic fallback for attributes that exist on the live
        # object but aren't visible to the static MRO walk or instance
        # __dict__ check above.  This covers objects with custom storage
        # backends (e.g. threading.local uses a per-thread dict not
        # accessible via obj.__dict__) and C extensions that store data
        # outside the normal Python object layout.
        #
        # This is NOT the same as the C-level data descriptor fallback in
        # resolve_data_descriptor (step 2): that handles descriptors found
        # on the type MRO (like member_descriptor for __slots__), while this
        # handles attributes that aren't on the type MRO at all.
        #
        # Only safe when the class doesn't override __getattribute__,
        # otherwise we'd run arbitrary user code.
        if not self._object_has_getattribute:
            try:
                resolved = type(self.value).__getattribute__(self.value, name)
                source = self.maybe_wrap_nn_module_source_for_instance(tx, name, source)
                return VariableTracker.build(tx, resolved, source)
            except AttributeError:
                pass

        # Step 6: __getattr__ fallback.
        getattr_fn = self._check_for_getattr()
        if isinstance(getattr_fn, types.FunctionType):
            if (
                getattr_fn is unpatched_nn_module_getattr
                and isinstance(self, variables.UnspecializedNNModuleVariable)
                and istype(self.value._parameters, dict)  # type: ignore[attr-defined]
                and istype(self.value._buffers, dict)  # type: ignore[attr-defined]
                and istype(self.value._modules, dict)  # type: ignore[attr-defined]
            ):
                out = self.manually_trace_nn_module_getattr(tx, name)
            else:
                new_source = None
                if self.source:
                    new_source = AttrSource(self.source, "__getattr__")
                out = variables.UserMethodVariable(
                    getattr_fn, self, source=new_source
                ).call_function(tx, [variables.ConstantVariable.create(name)], {})

            if self.source and getattr_fn is torch.nn.Module.__getattr__:
                if isinstance(
                    out,
                    (
                        variables.UnspecializedNNModuleVariable,
                        variables.NNModuleVariable,
                    ),
                ):
                    out.set_nn_module_stack_source(  # type: ignore[attr-defined]
                        AttrSource(self.get_nn_module_stack_source(), name)  # type: ignore[attr-defined]
                    )
            return out

        elif getattr_fn is not None:
            unimplemented(
                gb_type="User-defined object with non-function __getattr__",
                context=f"object={self.value}, name={name}, getattr_fn={getattr_fn}",
                explanation=f"Found a non-function __getattr__ {getattr_fn} from a user-defined object {self.value} "
                f" when attempting to getattr `{name}`",
                hints=[
                    "Ensure the object's __getattr__ is a function type.",
                ],
            )

        # Step 7: AttributeError.
        raise_observed_exception(
            AttributeError,
            tx,
            args=[f"'{type(self.value).__name__}' object has no attribute '{name}'"],
        )