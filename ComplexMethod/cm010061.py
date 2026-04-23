def _impl_with_aoti_compile(self, op_name, dispatch_key=""):
        r"""Register the operator to use the AOTI-compiled implementation.

        Args:
            op_name: operator name (along with the overload) or OpOverload object.
            dispatch_key: dispatch key that the input function should be registered for. By default, it uses
                          the dispatch key that the library was created with.

        Example::

            >>> my_lib = Library("aten", "IMPL")
            >>> my_lib._impl_with_aoti_compile("div.Tensor", "CPU")
        """

        if dispatch_key == "":
            dispatch_key = self.dispatch_key
        # pyrefly: ignore [bad-argument-type]
        if not torch.DispatchKeySet(dispatch_key).has(torch._C.DispatchKey.Dense):
            raise AssertionError(
                f"dispatch_key {dispatch_key} does not have Dense in its keyset"
            )

        if isinstance(op_name, str):
            name = op_name
        elif isinstance(op_name, OpOverload):
            name = op_name._schema.name
            overload_name = op_name._schema.overload_name
            if overload_name != "":
                name = name + "." + overload_name
        else:
            raise RuntimeError(
                "_impl_with_aoti_compile should be passed either a name or an OpOverload object "
                "as the first argument"
            )

        key = self.ns + "/" + name.split("::")[-1] + "/" + dispatch_key
        if key in _impls:
            # TODO: in future, add more info about where the existing function is registered (this info is
            # today already returned by the C++ warning when _impl_with_aoti_compile is called but we error out before that)
            raise RuntimeError(
                "This is not allowed since there's already a kernel registered from python overriding {}"
                "'s behavior for {} dispatch key and {} namespace.".format(
                    name.split("::")[-1], dispatch_key, self.ns
                )
            )

        if self.m is None:
            raise AssertionError("Library object has been destroyed")
        impl_fn: Callable = self.m.impl_with_aoti_compile
        impl_fn(self.ns, name.split("::")[-1], dispatch_key)

        _impls.add(key)
        self._op_impls.add(key)