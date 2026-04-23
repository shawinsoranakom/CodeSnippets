def create_arg(self, a: Any) -> "Argument":
        """
        A method to specify the behavior of tracing when preparing values to
        be used as arguments to nodes in the ``Graph``.

        By default, the behavior includes:

        #. Iterate through collection types (e.g. tuple, list, dict) and recursively
           call ``create_args`` on the elements.
        #. Given a Proxy object, return a reference to the underlying IR ``Node``
        #. Given a non-Proxy Tensor object, emit IR for various cases:

            * For a Parameter, emit a ``get_attr`` node referring to that Parameter
            * For a non-Parameter Tensor, store the Tensor away in a special
              attribute referring to that attribute.

        This method can be overridden to support more types.

        Args:

            a (Any): The value to be emitted as an ``Argument`` in the ``Graph``.


        Returns:

            The value ``a`` converted into the appropriate ``Argument``
        """
        # The base tracer is used to construct Graphs when there is no associated
        # module hierarchy, so it can never create parameter references.
        # The default tracer adds the ability to refer to parameters when
        # tracing modules.
        if isinstance(a, torch.nn.Parameter):
            for n, p in self.root.named_parameters():
                if a is p:
                    return self.create_node("get_attr", n, (), {})
            raise NameError("parameter is not a member of this module")
        elif isinstance(a, torch.Tensor):
            for n_, p_ in self.root.named_buffers():
                if a is p_:
                    return self.create_node("get_attr", n_, (), {})
        elif isinstance(a, torch.nn.Module):
            for n_, p_ in self.root.named_modules():
                if a is p_:
                    return self.create_node("get_attr", n_, (), {})
        # For NamedTuple instances that appear literally as args, we emit
        # a node to construct the NamedTuple and use that Node as the argument.
        if isinstance(a, tuple) and hasattr(a, "_fields"):
            args = tuple(self.create_arg(elem) for elem in a)
            return self.create_node("call_function", a.__class__, args, {})

        # Tensors do not have a reliable string repr() from which they can be
        # constructed (and we probably don't want to rely on that, either), so
        # for any constant Tensor values we encounter, first search for if they
        # are an attribute of some module in the module hierarchy. If so, emit
        # a get_attr to retrieve that tensor. Otherwise, we'll store away the
        # tensor value into a special attribute on the Module s.t. we can
        # retrieve it with a get_attr.
        if isinstance(a, _constant_attribute_types) or (
            is_opaque_reference_type(type(a))
        ):
            qualname: str | None = self.tensor_attrs.get(a)

            # Tensor was not found in the Module hierarchy, stow it away in a
            # special attribute and set the qualname to refer to that
            if not qualname:
                if isinstance(a, torch.Tensor):
                    base_name = "_tensor_constant"
                elif isinstance(a, (FakeScriptObject, ScriptObject)):
                    base_name = "_torchbind_obj"
                elif isinstance(a, pytree.TreeSpec):
                    base_name = "_tree_spec_constant"
                elif is_opaque_type(type(a)):
                    base_name = "_opaque_obj"
                else:
                    raise RuntimeError(
                        f"cannot create constant arg for {a} of type {type(a)}."
                    )
                qualname = self.get_fresh_qualname(base_name)
                if not isinstance(qualname, str):
                    raise AssertionError(
                        f"Expected qualname to be str, got {type(qualname)}"
                    )
                self.tensor_attrs[a] = qualname
                setattr(self.root, qualname, a)

            return self.create_node("get_attr", qualname, (), {})

        if type(a) in _proxyable_classes:
            # This is an instance of a proxyable class for which we did not
            # witness its construction. Intern this as a constant attribute

            # TODO: binary search
            qualname = self.get_fresh_qualname(f"_{a.__class__.__name__}_constant_")
            if not isinstance(qualname, str):
                raise AssertionError(
                    f"Expected qualname to be str, got {type(qualname)}"
                )
            setattr(self.root, qualname, a)

            return self.create_node("get_attr", qualname, (), {})
        return super().create_arg(a)