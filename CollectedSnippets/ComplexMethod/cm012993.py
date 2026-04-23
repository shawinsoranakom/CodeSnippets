def prepare(self, model, config):
        r"""Prepares a model, by adding the parametrizations.

        Note::

            The model is modified inplace. If you need to preserve the original
            model, use copy.deepcopy.
        """
        self.model = model  # TODO: Need to figure out how to load without this.
        self.config = config

        # If no config -- try getting all the supported layers
        if self.config is None:
            self.make_config_from_model(model)

        # TODO: Remove the configuration by reference ('module')

        for module_config in self.config:
            if not isinstance(module_config, dict):
                raise AssertionError(
                    "config elements should be dicts not modules i.e.:"
                    "[{`tensor_fqn`: `foo.bar.weight`}, {`tensor_fqn`: ... }, ...]"
                )

            if not isinstance(self.defaults, dict):
                raise AssertionError("defaults must be a dict")
            local_args = copy.deepcopy(self.defaults)
            local_args.update(module_config)

            tensor_fqn = local_args.get("tensor_fqn", None)
            if tensor_fqn is None:
                raise AssertionError(
                    "tensor_fqn is a required argument in the sparsity config which"
                    "replaces previous `module` and [module]`fqn` arguments"
                )

            # populate all information from tensor_fqn
            info_from_tensor_fqn = get_arg_info_from_tensor_fqn(model, tensor_fqn)

            # check that whatever was put into local_args agrees with what was obtained
            # from tensor_fqn
            for key in info_from_tensor_fqn:
                if key in local_args:
                    if not (
                        info_from_tensor_fqn[key] == local_args[key]
                        or (
                            key == "tensor_fqn"
                            and "." + info_from_tensor_fqn[key] == local_args[key]
                        )
                        # info_from_tensor_fqn will chop leading '.' from tensor_fqn so ignore that
                    ):
                        raise AssertionError(
                            f"Given both `{key}` and `tensor_fqn` in the config, it is expected them to agree!"
                        )
            local_args.update(info_from_tensor_fqn)
            self.groups.append(local_args)
        self._prepare()