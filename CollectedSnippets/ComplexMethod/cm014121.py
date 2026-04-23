def wrap_numpy_ndarray(self, value: Any) -> VariableTracker:
        assert np is not None
        assert isinstance(value, np.ndarray)

        source = NumpyTensorSource(self.get_source())

        from torch._numpy import _util

        readonly = not value.flags.writeable
        if readonly:
            try:
                value.flags.writeable = True
            except ValueError:
                # One can not easily make nditer elements writable,
                # but warning is not the end of the world
                assert isinstance(value.base, np.nditer)
        tensor_value = None
        with torch_function_mode_stack_state_mgr.temp_restore_stack():
            try:
                tensor_value = _util._try_convert_to_tensor(value)
                if readonly:
                    from torch._prims_common import clone_preserve_strides

                    tensor_value = clone_preserve_strides(tensor_value)
            except NotImplementedError as e:
                # failed to convert to tensor, graph break
                unimplemented(
                    gb_type="failed to convert numpy.ndarray to Tensor",
                    context=str(value),
                    explanation="Exception encountered when attempting to convert numpy.ndarray to Tensor",
                    hints=[],
                    from_exc=e,
                )
        assert tensor_value is not None

        # We do this because we want the full behavior of guarding the numpy ndarray as if it were
        # a tensor. It's a little annoying to make a VT to throw out, but there's so many side effects here
        # that there's not another great way to do this atm.
        # This creates the right graphargs, as well as registration for guards in tensor names and shape env.
        LazyVariableTracker.realize_all(VariableBuilder(self.tx, source)(tensor_value))
        example_value = wrap_to_fake_tensor_and_record(
            tensor_value,
            tx=self.tx,
            is_tensor=False,
            source=source,
        )
        proxy = self.tx.output.root_tracer.create_graph_input(
            re.sub(r"[^a-zA-Z0-9]+", "_", self.name),
            type(tensor_value),
            example_value,
            source=source,
        )
        cache_real_value_when_export(self.tx, proxy, tensor_value)
        options = {"source": source}
        numpy_ndarray_variable = wrap_fx_proxy_cls(
            target_cls=NumpyNdarrayVariable,
            tx=self.tx,
            proxy=proxy,
            example_value=example_value,
            subclass_type=None,
            **options,
        )

        self.tx.output.input_source_to_var[source] = numpy_ndarray_variable
        # type: ignore[attr-defined]
        example_value = numpy_ndarray_variable.proxy.node.meta["example_value"]

        # pass_arg_as_tensor should be true because we are wrapping a np.ndarray as argument input, and it needs to be
        # converted to a tensor.
        grapharg = GraphArg(
            source,
            tensor_value,
            pass_arg_as_tensor=True,
            fake_tensor=example_value,
            is_tensor=True,
            example_strong_ref=tensor_value,
        )
        proxy.node.meta["grapharg"] = grapharg

        # TODO - Why do we need to set the source of the np ndarray vt back to
        # original source. Many tests fails.
        numpy_ndarray_variable.source = self.source

        return numpy_ndarray_variable