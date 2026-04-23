def var_getattr(self, tx: "InstructionTranslator", name: str) -> VariableTracker:
        source = self.source and AttrSource(self.source, name)

        base = tx.output.get_submodule(self.module_key)
        # NB: We look up attributes in __dict__ directly, bypassing any custom
        # __getattribute__. Custom __getattribute__ is only traced through as a
        # fallback (via _custom_getattr_fallback) for attributes not found here.
        base_dict = object.__getattribute__(base, "__dict__")
        object_member = True
        all_class_attribute_names = set()
        for x in inspect.getmro(base.__class__):
            all_class_attribute_names.update(x.__dict__.keys())

        if not self.source:
            unimplemented(
                gb_type="getattr with no source",
                context=f"var_getattr {self} {name}",
                explanation="Dynamo does not know how to access an attribute "
                "on an `nn.Module` instance that lacks a source. This is "
                "usually an internal error in Dynamo.",
                hints=[*graph_break_hints.DYNAMO_BUG],
            )

        if name == "__dict__":
            return self.get_dict_vt(tx)

        subobj = None
        if name in base_dict:
            subobj = base_dict[name]
        elif (
            "_modules" in base_dict
            and name in base_dict["_modules"]
            and name not in all_class_attribute_names
        ):
            subobj = base_dict["_modules"][name]
        elif "_parameters" in base_dict and name in base_dict["_parameters"]:
            subobj = base_dict["_parameters"][name]
        elif "_buffers" in base_dict and name in base_dict["_buffers"]:
            subobj = base_dict["_buffers"][name]
        else:
            try:
                subobj = inspect.getattr_static(base, name)
                object_member = False
            except AttributeError:
                # see if we can fallback to __getattr__, which is not checked by getattr_static
                result = self._custom_getattr_fallback(
                    base=base, tx=tx, name=name, obj_source=self.source
                )
                if result is not None:
                    return result
                # if we can't find a __getattr__, we can't parse this, raise attribute error
                raise_observed_exception(
                    AttributeError,
                    tx,
                    args=[f"'{type(base).__name__}' object has no attribute '{name}'"],
                )

        if name == "forward":
            guard_to_detect_forward_monkeypatching(self.source, base)

        if name == "__class__" and not object_member:
            return VariableTracker.build(tx, base.__class__, source=source)

        if object_member:
            out = VariableTracker.build(tx, subobj, NNModuleSource(source))  # type: ignore[arg-type]

            if isinstance(out, (NNModuleVariable, UnspecializedNNModuleVariable)):
                # nn_module_stack source is BC surface area. Ensure that
                # mod._modules["linear"] is reflected as mod.linear for
                # nn_module_stack.
                out.set_nn_module_stack_source(
                    AttrSource(self.get_nn_module_stack_source(), name)
                )
            return out

        else:
            if istype(subobj, property):
                if self.source:
                    # Read the class attribute to reach the property
                    source = AttrSource(AttrSource(self.source, "__class__"), name)
                    # Get the getter function
                    source = AttrSource(source, "fget")
                return variables.UserFunctionVariable(
                    subobj.fget,  # pyrefly: ignore[bad-argument-type]
                    source=source,
                ).call_function(tx, [(self)], {})
            elif istype(subobj, classmethod):
                return variables.UserMethodVariable(
                    subobj.__func__,
                    variables.UserDefinedObjectVariable(type(base)),
                    source=source,
                )
            elif istype(subobj, staticmethod):
                return variables.UserFunctionVariable(
                    subobj.__get__(base),
                    source=source,
                )
            elif istype(subobj, types.FunctionType):
                return variables.UserMethodVariable(subobj, self, source=source)
            elif is_safe_constant(subobj) or istensor(subobj):
                # Support possibly common cases of class members
                return VariableTracker.build(tx, subobj, NNModuleSource(source))  # type: ignore[arg-type]
            else:
                unimplemented(
                    gb_type="Unsupported nn.Module attribute type",
                    context=f"nn.Module subclass: {typestr(base)}, name: {name}, attribute type: {typestr(subobj)}",
                    explanation=f"Dynamo does not support tracing nn.Module attributes of type `{typestr(subobj)}`",
                    hints=[
                        f"Refactor your code so that `{name}` (type `{typestr(subobj)}`) is not an attribute of `{typestr(base)}`",
                        "Currently supported attribute types are methods, classmethods, staticmethods, "
                        "properties, constants, and tensors.",
                        *graph_break_hints.SUPPORTABLE,
                    ],
                )

        return super().var_getattr(tx, name)