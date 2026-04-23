def squash_mask(
        self,
        params_to_keep: tuple[str, ...] | None = None,
        params_to_keep_per_layer: dict[str, tuple[str, ...]] | None = None,
        *args,
        **kwargs,
    ):
        r"""Squashes the sparse masks into the appropriate tensors.

        If either the `params_to_keep` or `params_to_keep_per_layer` is set,
        the module will have a `sparse_params` dict attached to it.

        Args:
            params_to_keep: List of keys to save in the module or a dict
                            representing the modules and keys that will have
                            sparsity parameters saved
            params_to_keep_per_layer: Dict to specify the params that should be
                            saved for specific layers. The keys in the dict
                            should be the module fqn, while the values should
                            be a list of strings with the names of the variables
                            to save in the `sparse_params`

        Examples:
            >>> # xdoctest: +SKIP("locals are undefined")
            >>> # Don't save any sparse params
            >>> sparsifier.squash_mask()
            >>> hasattr(model.submodule1, "sparse_params")
            False

            >>> # Keep sparse params per layer
            >>> sparsifier.squash_mask(
            ...     params_to_keep_per_layer={
            ...         "submodule1.linear1": ("foo", "bar"),
            ...         "submodule2.linear42": ("baz",),
            ...     }
            ... )
            >>> print(model.submodule1.linear1.sparse_params)
            {'foo': 42, 'bar': 24}
            >>> print(model.submodule2.linear42.sparse_params)
            {'baz': 0.1}

            >>> # Keep sparse params for all layers
            >>> sparsifier.squash_mask(params_to_keep=("foo", "bar"))
            >>> print(model.submodule1.linear1.sparse_params)
            {'foo': 42, 'bar': 24}
            >>> print(model.submodule2.linear42.sparse_params)
            {'foo': 42, 'bar': 24}

            >>> # Keep some sparse params for all layers, and specific ones for
            >>> # some other layers
            >>> sparsifier.squash_mask(
            ...     params_to_keep=("foo", "bar"),
            ...     params_to_keep_per_layer={"submodule2.linear42": ("baz",)},
            ... )
            >>> print(model.submodule1.linear1.sparse_params)
            {'foo': 42, 'bar': 24}
            >>> print(model.submodule2.linear42.sparse_params)
            {'foo': 42, 'bar': 24, 'baz': 0.1}
        """
        for config in self.groups:
            module = config["module"]
            tensor_name = config["tensor_name"]
            parametrize.remove_parametrizations(
                module, tensor_name, leave_parametrized=True
            )
            sparse_params = {}
            if params_to_keep is not None:
                global_params = {k: config[k] for k in params_to_keep}
                sparse_params.update(global_params)
            if params_to_keep_per_layer is not None:
                params = params_to_keep_per_layer.get(config["module_fqn"], None)
                if params is not None:
                    per_layer_params = {k: config[k] for k in params}
                    sparse_params.update(per_layer_params)
            if sparse_params:
                # TODO handle multiple tensor being quantized on a single module, where to store sparse_params?
                module.sparse_params = sparse_params