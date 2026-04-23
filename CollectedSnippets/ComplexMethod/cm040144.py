def add_endpoint(self, name, fn, input_signature=None, **kwargs):
        if name in self._endpoint_names:
            raise ValueError(f"Endpoint name '{name}' is already taken.")

        if backend.backend() != "jax":
            if "jax2tf_kwargs" in kwargs or "is_static" in kwargs:
                raise ValueError(
                    "'jax2tf_kwargs' and 'is_static' are only supported with "
                    f"the jax backend. Current backend: {backend.backend()}"
                )

        # The fast path if `fn` is already a `tf.function`.
        if input_signature is None:
            if isinstance(fn, tf.types.experimental.GenericFunction):
                if not fn._list_all_concrete_functions():
                    raise ValueError(
                        f"The provided tf.function '{fn}' "
                        "has never been called. "
                        "To specify the expected shape and dtype "
                        "of the function's arguments, "
                        "you must either provide a function that "
                        "has been called at least once, or alternatively pass "
                        "an `input_signature` argument in `add_endpoint()`."
                    )
                decorated_fn = fn
            else:
                raise ValueError(
                    "If the `fn` argument provided is not a `tf.function`, "
                    "you must provide an `input_signature` argument to "
                    "specify the shape and dtype of the function arguments. "
                    "Example:\n\n"
                    "export_archive.add_endpoint(\n"
                    "    name='call',\n"
                    "    fn=model.call,\n"
                    "    input_signature=[\n"
                    "        keras.InputSpec(\n"
                    "            shape=(None, 224, 224, 3),\n"
                    "            dtype='float32',\n"
                    "        )\n"
                    "    ],\n"
                    ")"
                )
            setattr(self._tf_trackable, name, decorated_fn)
            self._endpoint_names.append(name)
            return decorated_fn

        input_signature = tree.map_structure(
            make_tf_tensor_spec, input_signature
        )
        decorated_fn = self._backend_add_endpoint(
            name, fn, input_signature, **kwargs
        )
        self._endpoint_signatures[name] = input_signature
        setattr(self._tf_trackable, name, decorated_fn)
        self._endpoint_names.append(name)
        return decorated_fn